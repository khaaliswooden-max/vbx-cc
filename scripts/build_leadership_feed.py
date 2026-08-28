#!/usr/bin/env python3
"""
build_leadership_feed.py — redact internal content before publishing.

WHY THIS EXISTS
The leadership dashboard is served from GitHub Pages, which is PUBLIC and
search-indexable (CLAUDE.md Hard Rule #7 and the owner's 2026-06-05 exception,
which warns about exactly this). Anything left in the workbook the Pages build
copies is published with it.

WHAT IS WITHHELD, AND WHY
  * Pipeline!J (Notes) — ~21k characters of internal capture prose: teaming
    partner names, Pwin scores and EV math, bench size, no-bid rationale, and
    (in one row) the internal framework names Hard Rule #8 forbids externally.
    This was being served publicly before 2026-08-28; redacting it is the fix.
  * Opportunity_Detail BD columns — bd_posture, teaming_status, next_milestone,
    milestone_owner, win_theme, staffing_gap. The sheet's TECHNICAL half (scope,
    capabilities, LCATs, compliance gates, place/period of performance, response
    due) IS published, so operations and delivery get the live link they need
    without putting competitive posture on the open web (owner decision,
    2026-08-28).

Values in the published fields state the SOLICITATION's requirement; VBX's own
standing against it lives in the withheld fields. Keep it that way when editing
the feed: "SOC 2 Type 2" is publishable, "SOC 2 Type 2 — not held" is not.

WHY THIS EDITS THE ZIP INSTEAD OF USING OPENPYXL
An .xlsx is a zip of XML parts. openpyxl does not preserve CACHED FORMULA
RESULTS, and the dashboard reads only those (SheetJS `cell.v`): nine of the
eleven cells it pulls via getCell() are formulas — Targets!C11-C14 (confirmed
revenue, run-rate P/L, break-even gap, ARR gap) and Targets!D34-D38 (BD monthly
targets). A load/save on the publish path would blank all nine. So this edits the
package directly and copies every untouched part through byte-for-byte.

Blanking a cell is not enough on its own: Excel stores text in a workbook-wide
shared string table that survives the cell, so orphaned entries are blanked too.

TWO GUARDS, both fatal — no output is written if either trips:
  * leak scan — no value unique to a redacted cell may appear anywhere in the
    package. Content, not sheet listings: "the sheet isn't listed" says nothing
    about whether its text is still in the file.
  * forbidden-term scan — Hard Rule #8 names must never appear in a served
    artifact. This admits no exception and no override.

    python scripts/build_leadership_feed.py [in.xlsx] [out.xlsx]

Defaults: VBX_Command_Center_v1.1.xlsx -> data/leadership_feed.xlsx
"""
from __future__ import annotations

import posixpath
import re
import shutil
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape, unescape

import openpyxl
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline_feed as pf  # noqa: E402

# Whole sheets removed from the published copy. None today — Opportunity_Detail
# is now published in redacted form — but the machinery stays for future
# internal-only sheets.
STRIP_SHEETS: tuple[str, ...] = ()

# Disclosure policy is an ALLOWLIST, deliberately: name the columns that MAY be
# published and everything else in the sheet is withheld. Fail-closed — a column
# added to either sheet later is withheld until someone classifies it, rather
# than published because nobody remembered to redact it.
PUBLISH_COLUMNS: dict[str, tuple[int, ...]] = {
    # A=OppID B=Name C=Client D=NAICS E=Stage F=Value G=Identified H=StageDate
    # I=Owner | J=Notes withheld (internal capture prose)
    "Pipeline": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    # A=OppID B=Name E=ResponseDue I=Scope J=Capabilities K=LaborCats
    # L=ComplianceGates M=PlaceOfPerf N=PeriodOfPerf
    # withheld: C=BDPosture D=TeamingStatus F=NextMilestone G=MilestoneOwner
    #           H=WinTheme O=StaffingGap
    "Opportunity_Detail": (1, 2, 5, 9, 10, 11, 12, 13, 14),
    # --- partner-bearing sheets (owner decision, 2026-08-28) ---
    # Counts, dates, classifications and set-aside/vertical mix stay public so
    # the BD cadence KPIs keep working; the identities behind them do not.
    # These carry NAMED INDIVIDUALS at third-party companies and VBX's private
    # PRIORITY/BENCH/WATCHLIST/FILED assessment of them.
    # A=Date D=Type G=Owner | withheld B=Partner C=Attendees E=Outcome F=NextStep
    "Meetings": (1, 4, 7),
    # A=# D=SetAside E=ScreenDate F=NDADate G=Vertical H=Classification
    # I=DisplayDate | withheld B=Company C=Contact
    "Screenings": (1, 4, 5, 6, 7, 8, 9),
    # A=# D=Date F=Status G=Classification
    # withheld B=Entity C=Contact E=Filename (filenames embed personal names)
    "NDAs": (1, 4, 6, 7),
    # A=# D=Date E=Type G=Status | withheld B=Party C=Contact F=Filename H=Notes
    "Agreements": (1, 4, 5, 7),
}


def redaction_plan(src: Path) -> dict[str, tuple[int, ...]]:
    """Columns to blank = every used column NOT on that sheet's allowlist."""
    wb = openpyxl.load_workbook(src, data_only=False)
    plan = {}
    for sheet, allowed in PUBLISH_COLUMNS.items():
        if sheet not in wb.sheetnames:
            continue
        used = wb[sheet].max_column
        plan[sheet] = tuple(c for c in range(1, used + 1) if c not in allowed)
    return plan

# Hard Rule #8: never in an external-facing artifact. No exception exists.
FORBIDDEN_TERMS = ("CAHSP", "GRHD")

WORKBOOK_PART = "xl/workbook.xml"
WORKBOOK_RELS = "xl/_rels/workbook.xml.rels"
CONTENT_TYPES = "[Content_Types].xml"
SHARED_STRINGS = "xl/sharedStrings.xml"
APP_PROPS = "docProps/app.xml"
CALC_CHAIN = "xl/calcChain.xml"
# The leak scan reads text CONTENT rather than raw package bytes, so short
# values no longer risk matching markup and the floor can sit low enough to
# cover person and company names ("Susan Rouse" is 11 characters). Values below
# SHORT_VALUE_LEN are matched on word boundaries to avoid catching a fragment
# of a longer published word.
LEAK_MIN_LEN = 3
SHORT_VALUE_LEN = 8

SHARED_CELL = re.compile(r'<c\b[^>]*\bt="s"[^>]*?>(.*?)</c>', re.S)
SI_ENTRY = re.compile(r"<si\b[^>]*/>|<si\b.*?</si>", re.S)
V_INT = re.compile(r"<v>(\d+)</v>")
ANY_CELL = re.compile(r'<c\b([^>]*?)/>|<c\b([^>]*?)>(.*?)</c>', re.S)
HYPERLINK = re.compile(r'<hyperlink\b[^>]*/>|<hyperlink\b[^>]*>.*?</hyperlink>', re.S)
TEXT_NODE = re.compile(r"<t\b[^>]*>(.*?)</t>", re.S)
REF_ATTR = re.compile(r'r="([A-Z]+)(\d+)"')
STYLE_ATTR = re.compile(r'(\ss="\d+")')


def _resolve(target: str, base_part: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(base_part), target))


def _rels_part_for(part: str) -> str:
    d, name = posixpath.split(part)
    return posixpath.join(d, "_rels", name + ".rels")


def _referenced_parts(zf: zipfile.ZipFile, rels_part: str) -> set[str]:
    if rels_part not in zf.namelist():
        return set()
    xml = zf.read(rels_part).decode("utf-8")
    out = set()
    for m in re.finditer(r"<Relationship\b[^>]*>", xml):
        tag = m.group(0)
        if 'TargetMode="External"' in tag:
            continue
        t = re.search(r'Target="([^"]+)"', tag)
        if t:
            out.add(_resolve(t.group(1), rels_part.replace("/_rels/", "/").replace(".rels", "")))
    return out


def redact_cells(xml: str, columns: set[str], first_row: int) -> tuple[str, int]:
    """Blank the given columns' cells from the header row down, keeping styles.

    The header is blanked too: a column label ("Internal Pwin", "Win Theme") can
    disclose on its own, and the dashboard parses by column index, not by name.

    A formula cell is never blanked — that would change what the workbook
    computes. None of the redacted columns hold formulas; this asserts it.
    """
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        attrs = m.group(1) if m.group(1) is not None else m.group(2)
        body = m.group(3) or ""
        ref = REF_ATTR.search(attrs or "")
        if not ref or ref.group(1) not in columns or int(ref.group(2)) < first_row:
            return m.group(0)
        if "<f>" in body or "<f " in body:
            raise SystemExit(f"ABORT: refusing to blank formula cell {ref.group(1)}{ref.group(2)}")
        if not body.strip() and m.group(1) is not None:
            return m.group(0)  # already empty
        style = STYLE_ATTR.search(attrs or "")
        count += 1
        return f'<c r="{ref.group(1)}{ref.group(2)}"{style.group(1) if style else ""}/>'

    xml = ANY_CELL.sub(repl, xml)

    # Excel turns a typed email address into a <hyperlink> whose target lives
    # outside the <c> element, so blanking the cell alone would leave a mailto
    # (and often a display name) behind. Drop hyperlinks anchored in a withheld
    # column. Anything this misses is caught by the leak scan, which reads
    # hyperlink text as content.
    def drop_link(m: re.Match) -> str:
        ref = re.search(r'ref="([A-Z]+)(\d+)"', m.group(0))
        if ref and ref.group(1) in columns and int(ref.group(2)) >= first_row:
            return ""
        return m.group(0)

    xml = HYPERLINK.sub(drop_link, xml)
    # CT_Hyperlinks requires at least one child, so an emptied container would
    # make Excel offer to repair the file. Drop it.
    xml = re.sub(r"<hyperlinks>\s*</hyperlinks>", "", xml)
    return xml, count


def blank_orphan_strings(sheet_parts: dict[str, bytes], sst_xml: str) -> tuple[str, int]:
    """Blank shared-string entries no remaining sheet cell references.

    Blanked IN PLACE, not removed, so every surviving index still resolves and no
    other sheet needs reindexing. A string still used by a retained cell stays.
    """
    entries = [m.group(0) for m in SI_ENTRY.finditer(sst_xml)]
    if not entries:
        return sst_xml, 0
    used: set[int] = set()
    for xml in sheet_parts.values():
        for m in SHARED_CELL.finditer(xml.decode("utf-8")):
            for v in V_INT.findall(m.group(1)):
                used.add(int(v))
    blanked = 0
    rebuilt = []
    for i, entry in enumerate(entries):
        if i in used:
            rebuilt.append(entry)
        else:
            rebuilt.append("<si><t/></si>")
            blanked += 1
    head = sst_xml[: sst_xml.index(entries[0])]
    tail = sst_xml[sst_xml.rindex(entries[-1]) + len(entries[-1]):]
    return head + "".join(rebuilt) + tail, blanked


def fix_app_props(xml: str, removed: list[str], remaining_sheets: int) -> str:
    """Drop stripped sheet names from docProps/app.xml and re-derive its counts."""
    for sheet in removed:
        xml = xml.replace(f"<vt:lpstr>{sheet}</vt:lpstr>", "")
    m = re.search(r"(<TitlesOfParts>\s*<vt:vector)([^>]*)(>)(.*?)(</vt:vector>\s*</TitlesOfParts>)", xml, re.S)
    if not m:
        return xml
    body = m.group(4)
    total = len(re.findall(r"<vt:lpstr>", body))
    attrs = re.sub(r'size="\d+"', f'size="{total}"', m.group(2))
    xml = xml[: m.start()] + m.group(1) + attrs + m.group(3) + body + m.group(5) + xml[m.end():]

    def set_count(text: str, label: str, count: int) -> str:
        return re.sub(
            rf"(<vt:lpstr>{re.escape(label)}</vt:lpstr>\s*</vt:variant>\s*<vt:variant>\s*<vt:i4>)\d+(</vt:i4>)",
            rf"\g<1>{count}\g<2>", text, flags=re.S)

    xml = set_count(xml, "Worksheets", remaining_sheets)
    xml = set_count(xml, "Named Ranges", max(total - remaining_sheets, 0))
    return xml


def build(src: Path, dst: Path, redact: dict[str, tuple[int, ...]]) -> tuple[list[str], int, int]:
    """Write the published copy. Returns (stripped sheets, cells blanked, strings blanked)."""
    with zipfile.ZipFile(src) as zin:
        names = zin.namelist()
        wb_xml = zin.read(WORKBOOK_PART).decode("utf-8")
        rels_xml = zin.read(WORKBOOK_RELS).decode("utf-8")

        rid_to_part = {}
        for m in re.finditer(r"<Relationship\b[^>]*>", rels_xml):
            rid = re.search(r'Id="([^"]+)"', m.group(0))
            tgt = re.search(r'Target="([^"]+)"', m.group(0))
            if rid and tgt:
                rid_to_part[rid.group(1)] = _resolve(tgt.group(1), WORKBOOK_PART)

        sheet_to_part, drop_parts, drop_rids, removed = {}, set(), set(), []
        for m in re.finditer(r"<sheet\b[^>]*/>", wb_xml):
            tag = m.group(0)
            name = re.search(r'name="([^"]+)"', tag)
            rid = re.search(r'r:id="([^"]+)"', tag)
            if not name or not rid:
                continue
            part = rid_to_part.get(rid.group(1))
            sheet_to_part[name.group(1)] = part
            if name.group(1) in STRIP_SHEETS:
                removed.append(name.group(1))
                wb_xml = wb_xml.replace(tag, "")
                drop_rids.add(rid.group(1))
                if part:
                    drop_parts.add(part)
                    sheet_rels = _rels_part_for(part)
                    own = _referenced_parts(zin, sheet_rels)
                    others: set[str] = set()
                    for rp in names:
                        if rp.endswith(".rels") and rp != sheet_rels:
                            others |= _referenced_parts(zin, rp)
                    drop_parts |= {p for p in own if p not in others}
                    if sheet_rels in names:
                        drop_parts.add(sheet_rels)

        for sheet in removed:
            for dm in re.finditer(r"<definedName\b[^>]*>.*?</definedName>", wb_xml, re.S):
                if re.search(rf"(^|[^A-Za-z0-9_]){re.escape(sheet)}!", dm.group(0)):
                    wb_xml = wb_xml.replace(dm.group(0), "")
        for rid in drop_rids:
            rels_xml = re.sub(rf'<Relationship\b[^>]*Id="{re.escape(rid)}"[^>]*/>', "", rels_xml)

        # --- blank redacted cells in place ---
        edited: dict[str, bytes] = {}
        cells_blanked = 0
        for sheet, cols in redact.items():
            part = sheet_to_part.get(sheet)
            if not part or part in drop_parts or part not in names:
                continue
            letters = {get_column_letter(c) for c in cols}
            xml = zin.read(part).decode("utf-8")
            xml, n = redact_cells(xml, letters, pf.HEADER_ROW)
            edited[part] = xml.encode("utf-8")
            cells_blanked += n

        if CALC_CHAIN in names and removed:
            drop_parts.add(CALC_CHAIN)
            crid = next((r for r, p in rid_to_part.items() if p == CALC_CHAIN), None)
            if crid:
                rels_xml = re.sub(rf'<Relationship\b[^>]*Id="{re.escape(crid)}"[^>]*/>', "", rels_xml)

        # --- purge orphaned shared strings, using the REDACTED sheet bodies ---
        sst_xml, strings_blanked = None, 0
        if SHARED_STRINGS in names and SHARED_STRINGS not in drop_parts:
            surviving = {
                n: edited.get(n) or zin.read(n)
                for n in names
                if n.startswith("xl/worksheets/") and n.endswith(".xml") and n not in drop_parts
            }
            sst_xml, strings_blanked = blank_orphan_strings(
                surviving, zin.read(SHARED_STRINGS).decode("utf-8"))

        app_xml = None
        if APP_PROPS in names and removed:
            raw = zin.read(APP_PROPS).decode("utf-8")
            if any(s in raw for s in removed):
                app_xml = fix_app_props(raw, removed, len(re.findall(r"<sheet\b", wb_xml)))

        ct_xml = zin.read(CONTENT_TYPES).decode("utf-8")
        for part in drop_parts:
            ct_xml = re.sub(rf'<Override\b[^>]*PartName="/{re.escape(part)}"[^>]*/>', "", ct_xml)

        dst.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename in drop_parts:
                    continue
                if item.filename == WORKBOOK_PART:
                    data = wb_xml.encode("utf-8")
                elif item.filename == WORKBOOK_RELS:
                    data = rels_xml.encode("utf-8")
                elif item.filename == CONTENT_TYPES:
                    data = ct_xml.encode("utf-8")
                elif item.filename == SHARED_STRINGS and sst_xml is not None:
                    data = sst_xml.encode("utf-8")
                elif item.filename == APP_PROPS and app_xml is not None:
                    data = app_xml.encode("utf-8")
                elif item.filename in edited:
                    data = edited[item.filename]
                else:
                    data = zin.read(item.filename)  # untouched, verbatim
                zout.writestr(item, data)
    return removed, cells_blanked, strings_blanked


def withheld_values(src: Path, redact: dict[str, tuple[int, ...]]) -> tuple[set[str], set[str]]:
    """(values in redacted cells, values anywhere else) from the SOURCE workbook."""
    wb = openpyxl.load_workbook(src, data_only=False)
    withheld, retained = set(), set()
    for ws in wb.worksheets:
        cols = set(redact.get(ws.title, ()))
        stripped = ws.title in STRIP_SHEETS
        for row in ws.iter_rows():
            for c in row:
                if not isinstance(c.value, str) or not c.value.strip():
                    continue
                hidden = stripped or (c.column in cols and c.row >= pf.HEADER_ROW)
                (withheld if hidden else retained).add(c.value.strip())
    return withheld, retained


def published_text(dst: Path) -> str:
    """Every piece of human-readable TEXT the published package can surface.

    Deliberately not the raw zip bytes: styles and theme parts are markup noise
    that forces the length floor up, and the floor is what let short names slip
    past. This gathers the surfaces text can actually reach a reader through —
    shared strings (including entries no cell references), inline cell strings,
    cell comments, hyperlink targets and their display/tooltip text, and the
    document properties.
    """
    chunks: list[str] = []
    with zipfile.ZipFile(dst) as z:
        for name in z.namelist():
            if not (name.endswith(".xml") or name.endswith(".rels")):
                continue
            if name.startswith(("xl/theme/", "xl/styles")):
                continue
            xml = z.read(name).decode("utf-8", "ignore")
            chunks.extend(TEXT_NODE.findall(xml))
            if name.endswith(".rels"):
                chunks.extend(re.findall(r'Target="([^"]+)"', xml))
            for attr in ("display", "tooltip"):
                chunks.extend(re.findall(rf'{attr}="([^"]*)"', xml))
            if name.startswith("docProps/"):
                chunks.extend(re.findall(r">([^<]+)<", xml))
    return "\n".join(unescape(c) for c in chunks)


def leak_scan(dst: Path, withheld: set[str], retained: set[str]) -> list[str]:
    """Withheld values that still surface as text in the published package."""
    candidates = {v for v in withheld - retained
                  if len(v) >= LEAK_MIN_LEN and not any(v in r for r in retained)}
    if not candidates:
        return []
    text = published_text(dst)
    found = []
    for v in sorted(candidates):
        if len(v) < SHORT_VALUE_LEN:
            if re.search(rf"(?<!\w){re.escape(v)}(?!\w)", text):
                found.append(v)
        elif v in text:
            found.append(v)
    return found


def forbidden_scan(dst: Path) -> list[str]:
    """Hard Rule #8 terms present anywhere in the published package.

    Stays on the RAW bytes, unlike the leak scan: these terms must not appear
    anywhere at all, including in parts the leak scan deliberately skips.
    """
    with zipfile.ZipFile(dst) as z:
        blob = b"".join(z.read(n) for n in z.namelist()).decode("utf-8", "ignore")
    return [t for t in FORBIDDEN_TERMS if t in blob]


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = Path(args[0] if len(args) > 0 else "VBX_Command_Center_v1.1.xlsx")
    dst = Path(args[1] if len(args) > 1 else "data/leadership_feed.xlsx")

    if not src.exists():
        print(f"ERROR: source workbook not found: {src}")
        return 1

    wb = openpyxl.load_workbook(src, data_only=False)
    before = list(wb.sheetnames)
    dangling = sorted(
        cell for cell in pf.formula_set(wb)
        for sheet in STRIP_SHEETS
        if sheet in str(wb[cell.split("!")[0]][cell.split("!")[1]].value))
    if dangling:
        print("ABORT: formulas reference a sheet slated for stripping:", dangling[:10])
        return 2

    redact = redaction_plan(src)
    withheld, retained = withheld_values(src, redact)
    removed, cells, strings = build(src, dst, redact)

    out = openpyxl.load_workbook(dst, data_only=False)
    expected = [s for s in before if s not in removed]
    if out.sheetnames != expected:
        print(f"ABORT: sheet list changed unexpectedly.\n  got:      {out.sheetnames}\n  expected: {expected}")
        dst.unlink(missing_ok=True)
        return 2

    # Independent of the redaction pass: assert the published sheet carries data
    # only in allowlisted columns. Catches a column that policy never classified.
    stray = []
    for sheet, allowed in PUBLISH_COLUMNS.items():
        if sheet not in out.sheetnames:
            continue
        ws = out[sheet]
        for row in ws.iter_rows(min_row=pf.HEADER_ROW):
            for c in row:
                if c.value not in (None, "") and c.column not in allowed:
                    stray.append(f"{sheet}!{c.coordinate}")
    if stray:
        print(f"ABORT: {len(stray)} cell(s) outside the publish allowlist survived: {stray[:8]}")
        dst.unlink(missing_ok=True)
        return 5

    forbidden = forbidden_scan(dst)
    if forbidden:
        print(f"ABORT: Hard Rule #8 term(s) present in the published package: {forbidden}")
        dst.unlink(missing_ok=True)
        return 4

    leaked = leak_scan(dst, withheld, retained)
    if leaked:
        print(f"ABORT: {len(leaked)} withheld value(s) still present in {dst}:")
        for v in leaked[:5]:
            print(f"  - {v[:100]}{'...' if len(v) > 100 else ''}")
        dst.unlink(missing_ok=True)
        return 3

    print(f"Leadership feed -> {dst}")
    if removed:
        print(f"  sheets stripped: {', '.join(removed)}")
    for sheet, cols in redact.items():
        allowed = PUBLISH_COLUMNS[sheet]
        print(f"  {sheet}: published {', '.join(get_column_letter(c) for c in allowed)}"
              f"  |  withheld {', '.join(get_column_letter(c) for c in cols) or '(none)'}")
    print(f"  {cells} cell(s) blanked, {strings} orphaned shared string(s) blanked")
    print(f"  leak scan: 0 of {len(withheld)} withheld value(s) survive")
    print(f"  Hard Rule #8 scan: clean ({', '.join(FORBIDDEN_TERMS)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
