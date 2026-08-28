#!/usr/bin/env python3
"""
pipeline_feed.py — shared helpers for the text-mergeable Pipeline feed.

WHY THIS EXISTS
The Command Center workbook (VBX_Command_Center_v1.1.xlsx) is a binary file.
Git cannot merge binaries, so two branches that each add a Pipeline row conflict
on the whole workbook and must be re-resolved by hand — and sequential OPP-IDs
collide every time. The feed fixes both problems:

  * data/pipeline_feed.jsonl is the append-only source of record for Pipeline
    rows. One JSON object per opportunity, ONE physical line each. Concurrent
    branches append different lines, so git auto-merges them — no binary conflict.
  * OPP-IDs are assigned deterministically at SYNC time (on main, the single
    serialization point), never hardcoded by racing authors — so IDs never collide.

The workbook stays the system of record the HTML reads (CLAUDE.md invariant); the
feed is just the mergeable input source for the Pipeline INPUT sheet. No formula
ever lives in the feed.

Feed record schema (all string unless noted):
    key            required, unique. Stable author-chosen handle (e.g. the
                   solicitation number "RFP 26-14" or a slug). For migrated rows
                   it equals the OPP-ID. It is what makes a record identifiable
                   independent of its assigned OPP-ID.
    opp_id         assigned by sync if absent/null. Frozen once assigned.
    name, client, naics, owner, notes
    stage          one of STAGES
    value          integer dollars or null
    date_identified, stage_date   ISO "YYYY-MM-DD"

BD POSTURE + TECHNICAL DETAIL (optional; added 2026-08-28)
The same record also carries the structured fields the operations and technical
teams need to plan support for a pursuit. These were previously buried in the
free-text `notes` blob, which the dashboard never rendered. They are written to a
SECOND sheet, Opportunity_Detail, keyed by OPP-ID — not to extra Pipeline
columns — so the Pipeline sheet keeps its 10-column contract with the workbook
and the HTML parser (CLAUDE.md Hard Rule #3).

    bd_posture             one of BD_POSTURES ("" / absent = not stated)
    teaming_status         one of TEAMING_STATUS
    response_due           ISO "YYYY-MM-DD" — when the response is DUE. Distinct
                           from stage_date, which is when the row last moved.
    next_milestone         next concrete action
    milestone_owner        who owns it
    win_theme              why we win / discriminator
    scope_summary          plain-language what VBX would actually deliver
    capabilities_required  list[str] — technical capabilities the work needs
    labor_categories       list[str] — LCATs the solicitation names
    compliance_gates       list[str] — CMMC L2, FedRAMP, HIPAA, SOC 2, 508...
    place_of_performance   onsite / remote / hybrid + location
    period_of_performance  base + options
    staffing_gap           where the bench is short today

List fields accept a JSON array (preferred) or a plain "; "-joined string; they
are serialized to the sheet as "; "-joined text. Because that join is what makes
the sheet round-trip back into the feed, an individual list ITEM may not itself
contain a semicolon — validate() rejects one, rather than letting the item split
in half on the way back. Use an em dash or a comma inside an item instead.

Sheet order mirrors feed order 1:1 — the sync writes records top-to-bottom.
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path

# Column order on the Pipeline sheet (header row 4, data from row 5).
# Must stay in lockstep with the workbook + HTML parser (CLAUDE.md Hard Rule #3).
COLUMNS = [
    "opp_id",           # A
    "name",             # B
    "client",           # C
    "naics",            # D
    "stage",            # E
    "value",            # F  (int or None)
    "date_identified",  # G  (date)
    "stage_date",       # H  (date)
    "owner",            # I
    "notes",            # J
]
DATE_FIELDS = ("date_identified", "stage_date")
STAGES = ("Identified", "Qualified", "Capture", "Submitted", "Awarded", "Lost", "No-Bid")

# === OPPORTUNITY DETAIL (BD posture + technical) === #
# Column order on the Opportunity_Detail sheet (header row 4, data from row 5).
# One row per Pipeline row, same order — row N here describes row N there.
DETAIL_COLUMNS = [
    "opp_id",                 # A  join key back to Pipeline
    "name",                   # B  echoed for readability in Excel
    "bd_posture",             # C
    "teaming_status",         # D
    "response_due",           # E  (date)
    "next_milestone",         # F
    "milestone_owner",        # G
    "win_theme",              # H
    "scope_summary",          # I
    "capabilities_required",  # J  (list)
    "labor_categories",       # K  (list)
    "compliance_gates",       # L  (list)
    "place_of_performance",   # M
    "period_of_performance",  # N
    "staffing_gap",           # O
]
DETAIL_HEADERS = [
    "Opp ID", "Opportunity Name", "BD Posture", "Teaming Status", "Response Due",
    "Next Milestone", "Milestone Owner", "Win Theme", "Scope Summary",
    "Capabilities Required", "Labor Categories", "Compliance Gates",
    "Place of Performance", "Period of Performance", "Staffing Gap",
]
# Detail fields the feed author sets (opp_id/name are already Pipeline fields).
DETAIL_FIELDS = [c for c in DETAIL_COLUMNS if c not in COLUMNS]
DETAIL_DATE_FIELDS = ("response_due",)
LIST_FIELDS = ("capabilities_required", "labor_categories", "compliance_gates")
LIST_SEP = "; "

BD_POSTURES = ("Prime", "Sub", "Prime or Sub", "Undecided", "Not pursuing")
TEAMING_STATUS = (
    "Solo", "Partner needed", "Partner identified", "In discussion", "NDA executed",
    "Teaming agreement executed", "Teaming declined", "N/A",
)

HEADER_ROW = 4
FIRST_DATA_ROW = 5
LAST_COL = len(COLUMNS)  # 10
SHEET = "Pipeline"

DETAIL_LAST_COL = len(DETAIL_COLUMNS)  # 15
DETAIL_SHEET = "Opportunity_Detail"
DETAIL_TITLE = "  OPPORTUNITY DETAIL  —  BD Posture & Technical Scope  "
DETAIL_BANNER = (
    "  One row per Pipeline opportunity, same order. BD posture + technical scope so "
    "operations and delivery can plan support. INTERNAL — not published to the "
    "leadership site."
)

_ID_RE = re.compile(r"^OPP-(\d+)$")


def id_num(opp_id: str | None) -> int | None:
    """Return the integer inside an 'OPP-0NN' id, or None."""
    if not opp_id:
        return None
    m = _ID_RE.match(str(opp_id).strip())
    return int(m.group(1)) if m else None


def format_id(n: int) -> str:
    return f"OPP-{n:03d}"


def parse_date(s):
    """ISO 'YYYY-MM-DD' (or None/'') -> datetime.date | None."""
    if s in (None, ""):
        return None
    if isinstance(s, datetime.date) and not isinstance(s, datetime.datetime):
        return s
    if isinstance(s, datetime.datetime):
        return s.date()
    return datetime.date.fromisoformat(str(s)[:10])


def iso_date(v):
    """datetime/date (or None) -> ISO 'YYYY-MM-DD' | None."""
    if v in (None, ""):
        return None
    if isinstance(v, datetime.datetime):
        return v.date().isoformat()
    if isinstance(v, datetime.date):
        return v.isoformat()
    return str(v)[:10]


def as_list(v) -> list[str]:
    """Normalize a list field to a list of non-empty strings.

    Accepts a JSON array (preferred in the feed) or a "; "-joined string, so a
    record hand-edited in either style round-trips the same way.
    """
    if v in (None, ""):
        return []
    if isinstance(v, str):
        return [part.strip() for part in v.split(";") if part.strip()]
    return [str(x).strip() for x in v if str(x).strip()]


def detail_cell(rec: dict, field: str):
    """Value to write into an Opportunity_Detail cell for `field`."""
    v = rec.get(field)
    if field in LIST_FIELDS:
        items = as_list(v)
        return LIST_SEP.join(items) if items else None
    if field in DETAIL_DATE_FIELDS:
        return parse_date(v)
    return v if v not in ("",) else None


def has_detail(rec: dict) -> bool:
    """True when the record carries any BD-posture / technical detail."""
    return any(rec.get(f) not in (None, "", []) for f in DETAIL_FIELDS)


def load_feed(path: str | Path) -> list[dict]:
    """Read JSONL feed into a list of dict records, preserving file order.

    Blank lines are ignored. Raises ValueError with the line number on bad JSON
    so a malformed concurrent merge fails loudly instead of silently dropping.
    """
    records: list[dict] = []
    p = Path(path)
    if not p.exists():
        return records
    for lineno, raw in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            records.append(json.loads(raw))
        except json.JSONDecodeError as e:
            raise ValueError(f"{p}: invalid JSON on line {lineno}: {e}") from e
    return records


def dump_feed(path: str | Path, records: list[dict]) -> None:
    """Write records as JSONL — one compact object per line, key order stable,
    trailing newline. Deterministic so re-dumps produce minimal diffs."""
    ordered_keys = ["key"] + COLUMNS + DETAIL_FIELDS
    lines = []
    for r in records:
        obj = {k: r[k] for k in ordered_keys if k in r}
        # keep any extra keys (forward-compatible) after the known ones
        for k in r:
            if k not in obj:
                obj[k] = r[k]
        lines.append(json.dumps(obj, ensure_ascii=False))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def assign_ids(records: list[dict]) -> tuple[list[dict], list[tuple[str, str]]]:
    """Freeze existing opp_ids; assign the next free OPP-ID to records lacking one,
    in feed order. Returns (records, assignments) where assignments is a list of
    (key, new_id). Deterministic: assignment depends only on feed content/order,
    so concurrent additions never collide once merged.
    """
    used = {id_num(r.get("opp_id")) for r in records if id_num(r.get("opp_id")) is not None}
    nxt = (max(used) + 1) if used else 1
    assignments: list[tuple[str, str]] = []
    for r in records:
        if not r.get("opp_id"):
            while nxt in used:
                nxt += 1
            new = format_id(nxt)
            r["opp_id"] = new
            used.add(nxt)
            assignments.append((r.get("key", new), new))
            nxt += 1
    return records, assignments


def validate(records: list[dict]) -> list[str]:
    """Return a list of human-readable problems (empty == valid)."""
    problems: list[str] = []
    seen_keys: dict[str, int] = {}
    seen_ids: dict[str, int] = {}
    for i, r in enumerate(records):
        where = f"record #{i + 1} (key={r.get('key', '?')})"
        if not r.get("key"):
            problems.append(f"{where}: missing required 'key'")
        else:
            if r["key"] in seen_keys:
                problems.append(f"{where}: duplicate key (also record #{seen_keys[r['key']] + 1})")
            seen_keys[r["key"]] = i
        oid = r.get("opp_id")
        if oid:
            if id_num(oid) is None:
                problems.append(f"{where}: opp_id '{oid}' is not OPP-0NN form")
            if oid in seen_ids:
                problems.append(f"{where}: duplicate opp_id {oid} (also record #{seen_ids[oid] + 1})")
            seen_ids[oid] = i
        st = r.get("stage")
        if st and st not in STAGES:
            problems.append(f"{where}: stage '{st}' not one of {STAGES}")
        for df in DATE_FIELDS:
            if r.get(df):
                try:
                    parse_date(r[df])
                except Exception:
                    problems.append(f"{where}: {df} '{r[df]}' is not ISO YYYY-MM-DD")
        if r.get("value") not in (None,) and not isinstance(r.get("value"), int):
            problems.append(f"{where}: value must be an integer or null")

        # --- BD posture + technical detail (all optional) ---
        posture = r.get("bd_posture")
        if posture and posture not in BD_POSTURES:
            problems.append(f"{where}: bd_posture '{posture}' not one of {BD_POSTURES}")
        teaming = r.get("teaming_status")
        if teaming and teaming not in TEAMING_STATUS:
            problems.append(f"{where}: teaming_status '{teaming}' not one of {TEAMING_STATUS}")
        for df in DETAIL_DATE_FIELDS:
            if r.get(df):
                try:
                    parse_date(r[df])
                except Exception:
                    problems.append(f"{where}: {df} '{r[df]}' is not ISO YYYY-MM-DD")
        for lf in LIST_FIELDS:
            v = r.get(lf)
            if v in (None, "", []):
                continue
            if not isinstance(v, (list, str)):
                problems.append(f"{where}: {lf} must be a JSON array of strings (or a '; '-joined string)")
            elif isinstance(v, list) and not all(isinstance(x, str) for x in v):
                problems.append(f"{where}: {lf} array must contain strings only")
            else:
                # The sheet stores these joined by "; ", so a semicolon inside an
                # item would split it in two on the way back out (a silent,
                # lossy round-trip). Catch it here instead.
                for item in as_list(v) if isinstance(v, list) else []:
                    if ";" in item:
                        problems.append(
                            f"{where}: {lf} item {item!r} contains a semicolon — "
                            f"it would split when the sheet is read back; use an em dash or comma"
                        )
        if r.get("milestone_owner") and not r.get("next_milestone"):
            problems.append(f"{where}: milestone_owner set with no next_milestone")
    return problems


def formula_set(wb) -> set[str]:
    """Set of 'Sheet!Cell' for every formula cell — used to prove no formula moved."""
    out = set()
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("="):
                    out.add(f"{ws.title}!{c.coordinate}")
    return out
