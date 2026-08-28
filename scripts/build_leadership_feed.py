#!/usr/bin/env python3
"""
build_leadership_feed.py — strip internal-only sheets before publishing.

WHY THIS EXISTS
The leadership dashboard is served from GitHub Pages, which is PUBLIC and
search-indexable (CLAUDE.md Hard Rule #7 and the owner's 2026-06-05 exception,
which warns about exactly this). The workbook carries the operational record, so
anything left in the file that the Pages build copies is published with it.

The Opportunity_Detail sheet added 2026-08-28 holds BD posture, win themes,
teaming status, compliance gaps, and staffing gaps for every pursuit. That is
internal planning material for the operations and delivery teams — it is not
leadership-summary content and must not be search-indexable. This script removes
it from the copy that gets published. The committed workbook is never modified.

The dashboard degrades cleanly without the sheet: its parser returns [] for a
missing sheet and every detail panel reads "Not yet recorded", so the published
leadership view keeps working exactly as it did before the sheet existed.

WHY THIS EDITS THE ZIP INSTEAD OF USING OPENPYXL
An .xlsx is a zip of XML parts. Removing a sheet with openpyxl means load + save,
and openpyxl does not preserve CACHED FORMULA RESULTS — it writes the formula
string but drops the last-computed value. The dashboard reads only cached values
(SheetJS `cell.v`), and nine of the eleven cells it pulls with getCell() are
formulas: Targets!C11-C14 (confirmed revenue, run-rate P/L, break-even gap, ARR
gap) and Targets!D34-D38 (the five BD monthly targets). An openpyxl round-trip on
the publish path would blank all nine and silently drop those KPIs to the
hardcoded defaults in the HTML.

So this operates on the package directly: it removes the sheet's parts and the
references to them, and copies every other part through byte-for-byte. Cached
values, styles, and everything else survive exactly as the source had them.

Safe to run repeatedly; it always writes a fresh copy from the source workbook.

    python scripts/build_leadership_feed.py [in.xlsx] [out.xlsx]

Defaults: VBX_Command_Center_v1.1.xlsx -> data/leadership_feed.xlsx

NOTE ON SCOPE: this strips the internal detail sheet only. The rest of the
workbook — partner, NDA, and revenue detail — is published as before under the
owner's standing exception. Widening the redaction is an owner decision, not a
default; add sheets to STRIP_SHEETS (or column-level redaction) when authorized.
"""
from __future__ import annotations

import posixpath
import re
import shutil
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline_feed as pf  # noqa: E402

# Sheets removed from the published copy. Nothing in the workbook references
# these, so removing them cannot orphan a formula.
STRIP_SHEETS = (pf.DETAIL_SHEET,)

WORKBOOK_PART = "xl/workbook.xml"
SHARED_STRINGS = "xl/sharedStrings.xml"
APP_PROPS = "docProps/app.xml"
# Minimum length for a string to be worth leak-scanning. Below this a value is
# either a vocabulary term (already blanked when orphaned) or too generic to
# match meaningfully against the package bytes.
LEAK_MIN_LEN = 12
WORKBOOK_RELS = "xl/_rels/workbook.xml.rels"
CONTENT_TYPES = "[Content_Types].xml"
# Cells whose text lives in the shared string table, e.g.
# <c r="B5" s="7" t="s"><v>142</v></c>
SHARED_CELL = re.compile(r'<c\b[^>]*\bt="s"[^>]*?>(.*?)</c>', re.S)
SI_ENTRY = re.compile(r"<si\b[^>]*/>|<si\b.*?</si>", re.S)
V_INT = re.compile(r"<v>(\d+)</v>")

# calcChain caches Excel's formula evaluation ORDER by sheet index. Removing a
# sheet invalidates those indices, so the part is dropped; Excel rebuilds it on
# next open and SheetJS never reads it. Cached VALUES live in the sheet parts and
# are untouched by this.
CALC_CHAIN = "xl/calcChain.xml"


def _resolve(target: str, base_part: str) -> str:
    """Resolve a relationship Target to a package part name."""
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(base_part), target))


def _rels_part_for(part: str) -> str:
    d, name = posixpath.split(part)
    return posixpath.join(d, "_rels", name + ".rels")


def _referenced_parts(zf: zipfile.ZipFile, rels_part: str) -> set[str]:
    """Parts targeted by a .rels file (external targets ignored)."""
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


def blank_orphan_strings(sheet_parts: dict[str, bytes], sst_xml: str) -> tuple[str, int]:
    """Blank shared-string entries no remaining sheet references.

    Excel (unlike openpyxl, which writes inline strings) stores cell TEXT in a
    workbook-wide table, xl/sharedStrings.xml. Deleting a worksheet part does not
    touch that table, so on an Excel-saved workbook every string the stripped
    sheet contributed — win themes, teaming status, staffing gaps — would still
    sit in the published file, readable by anyone who downloads it, even though
    the sheet no longer appears in the workbook.

    Entries are blanked IN PLACE rather than removed so every surviving index
    still resolves; the table keeps its length and no other sheet needs
    rewriting. A string the stripped sheet shared with a retained sheet stays,
    correctly — it is still on a published sheet.

    Returns (new sst xml, number of entries blanked).
    """
    entries = [m.group(0) for m in SI_ENTRY.finditer(sst_xml)]
    if not entries:
        return sst_xml, 0

    used: set[int] = set()
    for xml in sheet_parts.values():
        text = xml.decode("utf-8")
        for m in SHARED_CELL.finditer(text):
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

    head = sst_xml[: sst_xml.index(entries[0])] if entries else sst_xml
    tail = sst_xml[sst_xml.rindex(entries[-1]) + len(entries[-1]):]
    return head + "".join(rebuilt) + tail, blanked


def fix_app_props(xml: str, removed: list[str], remaining_sheets: int) -> str:
    """Drop stripped sheet names from docProps/app.xml and re-derive its counts.

    app.xml caches a list of part titles (worksheets, then named ranges) plus
    HeadingPairs counts for each category. Removing a title without updating the
    vector size and the matching count leaves a document that declares more parts
    than it lists — which Excel's file properties and some repair paths trust.

    Counts are RE-DERIVED from what actually remains rather than decremented, so
    the result is self-consistent no matter what was removed.
    """
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
            rf"\g<1>{count}\g<2>", text, flags=re.S,
        )

    xml = set_count(xml, "Worksheets", remaining_sheets)
    xml = set_count(xml, "Named Ranges", max(total - remaining_sheets, 0))
    return xml


def strip_sheets(src: Path, dst: Path, sheet_names) -> list[str]:
    """Remove sheets from the package, copying all other parts verbatim.

    Returns the list of sheet names actually removed.
    """
    removed: list[str] = []
    with zipfile.ZipFile(src) as zin:
        names = zin.namelist()
        wb_xml = zin.read(WORKBOOK_PART).decode("utf-8")
        rels_xml = zin.read(WORKBOOK_RELS).decode("utf-8")

        # rId -> part name, from the workbook's relationships
        rid_to_part = {}
        for m in re.finditer(r"<Relationship\b[^>]*>", rels_xml):
            tag = m.group(0)
            rid = re.search(r'Id="([^"]+)"', tag)
            tgt = re.search(r'Target="([^"]+)"', tag)
            if rid and tgt:
                rid_to_part[rid.group(1)] = _resolve(tgt.group(1), WORKBOOK_PART)

        drop_parts: set[str] = set()
        drop_rids: set[str] = set()
        for m in re.finditer(r"<sheet\b[^>]*/>", wb_xml):
            tag = m.group(0)
            name = re.search(r'name="([^"]+)"', tag)
            rid = re.search(r'r:id="([^"]+)"', tag)
            if not name or name.group(1) not in sheet_names:
                continue
            removed.append(name.group(1))
            wb_xml = wb_xml.replace(tag, "")
            if rid:
                drop_rids.add(rid.group(1))
                part = rid_to_part.get(rid.group(1))
                if part:
                    drop_parts.add(part)
                    sheet_rels = _rels_part_for(part)
                    # Drop the sheet's own rels, plus any part ONLY it referenced
                    # (drawings, comments, printerSettings) so nothing leaks.
                    own = _referenced_parts(zin, sheet_rels)
                    others: set[str] = set()
                    for rp in names:
                        if rp.endswith(".rels") and rp != sheet_rels:
                            others |= _referenced_parts(zin, rp)
                    drop_parts |= {p for p in own if p not in others}
                    if sheet_rels in names:
                        drop_parts.add(sheet_rels)

        if not removed:
            shutil.copyfile(src, dst)
            return removed

        # definedNames pointing at a stripped sheet would dangle.
        for m in re.finditer(r"<definedName\b[^>]*>.*?</definedName>", wb_xml, re.S):
            body = m.group(0)
            if any(re.search(rf"(^|[^A-Za-z0-9_]){re.escape(s)}!", body) for s in removed):
                wb_xml = wb_xml.replace(body, "")

        for rid in drop_rids:
            rels_xml = re.sub(rf'<Relationship\b[^>]*Id="{re.escape(rid)}"[^>]*/>', "", rels_xml)
            rels_xml = re.sub(rf'<Relationship\b[^>]*Id="{re.escape(rid)}"[^>]*>.*?</Relationship>',
                              "", rels_xml, flags=re.S)

        if CALC_CHAIN in names:
            drop_parts.add(CALC_CHAIN)
            calc_rid = next((r for r, p in rid_to_part.items() if p == CALC_CHAIN), None)
            if calc_rid:
                rels_xml = re.sub(rf'<Relationship\b[^>]*Id="{re.escape(calc_rid)}"[^>]*/>', "", rels_xml)

        ct_xml = zin.read(CONTENT_TYPES).decode("utf-8")
        for part in drop_parts:
            ct_xml = re.sub(rf'<Override\b[^>]*PartName="/{re.escape(part)}"[^>]*/>', "", ct_xml)

        # Purge the stripped sheet's text from the shared string table, which
        # deleting the worksheet part does NOT do (see blank_orphan_strings).
        sst_xml = None
        blanked = 0
        if SHARED_STRINGS in names and SHARED_STRINGS not in drop_parts:
            surviving = {
                n: zin.read(n)
                for n in names
                if n.startswith("xl/worksheets/") and n.endswith(".xml") and n not in drop_parts
            }
            sst_xml, blanked = blank_orphan_strings(surviving, zin.read(SHARED_STRINGS).decode("utf-8"))

        # The cached document-properties sheet list would still name the sheet.
        app_xml = None
        if APP_PROPS in names:
            raw = zin.read(APP_PROPS).decode("utf-8")
            if any(sheet in raw for sheet in removed):
                app_xml = fix_app_props(raw, removed, len(re.findall(r"<sheet\b", wb_xml)))

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
                else:
                    data = zin.read(item.filename)  # everything else, verbatim
                zout.writestr(item, data)
    if blanked:
        print(f"  blanked {blanked} orphaned shared string(s)")
    return removed


def leak_scan(src: Path, dst: Path, removed: list[str]) -> list[str]:
    """Values unique to a stripped sheet that still appear in the output package.

    This is the check that actually matters. Asserting the sheet is no longer
    LISTED proves nothing about whether its text is still in the file — a
    shared string table, a comment part, or a cached property can carry the
    content long after the worksheet is gone. So: take every string the stripped
    sheet held, subtract anything a retained sheet also holds (that text is
    published regardless), and confirm none of the remainder survives anywhere
    in the bytes we are about to publish.
    """
    wb = openpyxl.load_workbook(src, data_only=False)
    internal: set[str] = set()
    retained: set[str] = set()
    for ws in wb.worksheets:
        bucket = internal if ws.title in removed else retained
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.strip():
                    bucket.add(c.value.strip())

    # Only values unique to the stripped sheet, and long enough to match
    # meaningfully rather than collide with markup.
    candidates = {
        v for v in internal - retained
        if len(v) >= LEAK_MIN_LEN and not any(v in r for r in retained)
    }
    if not candidates:
        return []

    with zipfile.ZipFile(dst) as z:
        blob = b"".join(z.read(n) for n in z.namelist())
    found = []
    for v in sorted(candidates):
        needles = {v.encode("utf-8"), escape(v).encode("utf-8")}
        if any(n in blob for n in needles):
            found.append(v)
    return found


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = Path(args[0] if len(args) > 0 else "VBX_Command_Center_v1.1.xlsx")
    dst = Path(args[1] if len(args) > 1 else "data/leadership_feed.xlsx")

    if not src.exists():
        print(f"ERROR: source workbook not found: {src}")
        return 1

    # Read-only inspection: a formula pointing at a stripped sheet would become
    # #REF! once published. Refuse rather than publish a broken workbook.
    wb = openpyxl.load_workbook(src, data_only=False)
    before = list(wb.sheetnames)
    dangling = sorted(
        cell
        for cell in pf.formula_set(wb)
        for sheet in STRIP_SHEETS
        if sheet in str(wb[cell.split("!")[0]][cell.split("!")[1]].value)
    )
    if dangling:
        print("ABORT: formulas reference a sheet slated for stripping:", dangling[:10])
        return 2

    removed = strip_sheets(src, dst, set(STRIP_SHEETS))

    # Verify the result opens and lost exactly what we intended.
    out = openpyxl.load_workbook(dst, data_only=False)
    expected = [s for s in before if s not in removed]
    if out.sheetnames != expected:
        print(f"ABORT: sheet list changed unexpectedly.\n  got:      {out.sheetnames}\n  expected: {expected}")
        return 2

    # Content-level check: the sheet being gone from the listing is not the same
    # as its data being gone from the file. Refuse to publish if anything unique
    # to a stripped sheet survives anywhere in the package.
    leaked = leak_scan(src, dst, removed)
    if leaked:
        print(f"ABORT: {len(leaked)} value(s) unique to the stripped sheet still present in {dst}:")
        for v in leaked[:5]:
            print(f"  - {v[:100]}{'...' if len(v) > 100 else ''}")
        dst.unlink(missing_ok=True)
        return 3

    print(f"Leadership feed -> {dst}")
    print(f"  stripped: {', '.join(removed) if removed else 'nothing (sheet not present)'}")
    print(f"  kept {len(out.sheetnames)} sheet(s): {', '.join(out.sheetnames)}")
    if removed:
        print("  leak scan: no value unique to the stripped sheet survives in the package")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
