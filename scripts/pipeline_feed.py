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

HEADER_ROW = 4
FIRST_DATA_ROW = 5
LAST_COL = len(COLUMNS)  # 10
SHEET = "Pipeline"

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
    ordered_keys = ["key"] + COLUMNS
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
