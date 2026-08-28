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

Safe to run repeatedly; it always writes a fresh copy from the source workbook.

    python scripts/build_leadership_feed.py [in.xlsx] [out.xlsx]

Defaults: VBX_Command_Center_v1.1.xlsx -> data/leadership_feed.xlsx

NOTE ON SCOPE: this strips the internal detail sheet only. The rest of the
workbook — partner, NDA, and revenue detail — is published as before under the
owner's standing exception. Widening the redaction is an owner decision, not a
default; add sheets to STRIP_SHEETS (or column-level redaction) when authorized.
"""
from __future__ import annotations

import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline_feed as pf  # noqa: E402

# Sheets removed from the published copy. Nothing in the workbook references
# these, so removing them cannot orphan a formula.
STRIP_SHEETS = (pf.DETAIL_SHEET,)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = Path(args[0] if len(args) > 0 else "VBX_Command_Center_v1.1.xlsx")
    dst = Path(args[1] if len(args) > 1 else "data/leadership_feed.xlsx")

    if not src.exists():
        print(f"ERROR: source workbook not found: {src}")
        return 1

    wb = openpyxl.load_workbook(src, data_only=False)
    before = list(wb.sheetnames)

    # A formula pointing at a stripped sheet would become #REF! once published.
    # Refuse rather than publish a broken workbook.
    dangling = sorted(
        cell
        for cell in pf.formula_set(wb)
        for sheet in STRIP_SHEETS
        if sheet in str(wb[cell.split("!")[0]][cell.split("!")[1]].value)
    )
    if dangling:
        print("ABORT: formulas reference a sheet slated for stripping:", dangling[:10])
        return 2

    removed = []
    for sheet in STRIP_SHEETS:
        if sheet in wb.sheetnames:
            del wb[sheet]
            removed.append(sheet)

    expected = [s for s in before if s not in removed]
    if wb.sheetnames != expected:
        print(f"ABORT: sheet list changed unexpectedly.\n  got:      {wb.sheetnames}\n  expected: {expected}")
        return 2

    dst.parent.mkdir(parents=True, exist_ok=True)
    wb.save(dst)
    kept = len(wb.sheetnames)
    print(f"Leadership feed -> {dst}")
    print(f"  stripped: {', '.join(removed) if removed else 'nothing (sheet not present)'}")
    print(f"  kept {kept} sheet(s): {', '.join(wb.sheetnames)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
