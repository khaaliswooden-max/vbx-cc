#!/usr/bin/env python3
"""
sync_pipeline_from_feed.py — feed -> workbook Pipeline sheet (the merge point).

Reads data/pipeline_feed.jsonl and writes its rows into the Pipeline INPUT sheet
of the committed workbook, in feed order. Assigns OPP-IDs deterministically to any
record lacking one and writes the assignments back into the feed.

Safety guarantees (all asserted; non-zero exit on violation):
  * Only the Pipeline sheet's data cells change. No other sheet is touched.
  * The workbook's formula set is byte-identical before/after — no formula moves
    (upholds the CLAUDE.md workbook->HTML invariant).
  * Value-diff writer: cells are set only when their value actually changes, so
    re-syncing an already-synced feed is a no-op (idempotent), and a feed exported
    straight from the workbook produces zero changes (lossless migration).

Usage:
    python scripts/sync_pipeline_from_feed.py \
        [data/pipeline_feed.jsonl] [VBX_Command_Center_v1.1.xlsx] [--check]

--check  validate + assign-preview only; write nothing (used by CI on PRs).
"""
from __future__ import annotations

import sys
from copy import copy
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline_feed as pf  # noqa: E402

DATE_FMT = "mm/dd/yyyy"
VALUE_FMT = r'\$#,##0;"($"#,##0\);\-'


def _same(existing, desired, is_date: bool) -> bool:
    if is_date:
        return pf.iso_date(existing) == pf.iso_date(desired)
    return existing == desired


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_only = "--check" in sys.argv[1:]
    feed_path = args[0] if len(args) > 0 else "data/pipeline_feed.jsonl"
    wb_path = args[1] if len(args) > 1 else "VBX_Command_Center_v1.1.xlsx"

    records = pf.load_feed(feed_path)
    problems = pf.validate(records)
    if problems:
        print("FEED VALIDATION FAILED:")
        for p in problems:
            print("  -", p)
        return 1

    records, assignments = pf.assign_ids(records)
    # validate again post-assignment (catches any id collision introduced)
    problems = pf.validate(records)
    if problems:
        print("FEED VALIDATION FAILED (post-assign):")
        for p in problems:
            print("  -", p)
        return 1
    for key, new_id in assignments:
        print(f"assigned {new_id} to key '{key}'")

    if check_only:
        print(f"--check OK: {len(records)} records, {len(assignments)} new id(s) would be assigned")
        return 0

    wb = openpyxl.load_workbook(wb_path, data_only=False)
    ws = wb[pf.SHEET]
    before_formulas = pf.formula_set(wb)

    # current last populated data row (template for styling new rows)
    cur_last = pf.HEADER_ROW
    for r in range(pf.FIRST_DATA_ROW, ws.max_row + 1):
        if any(ws.cell(r, c).value not in (None, "") for c in range(1, pf.LAST_COL + 1)):
            cur_last = r
    template_row = cur_last if cur_last >= pf.FIRST_DATA_ROW else None

    changed = 0
    for i, rec in enumerate(records):
        row = pf.FIRST_DATA_ROW + i
        is_new_row = row > cur_last
        for c, field in enumerate(pf.COLUMNS, 1):
            is_date = field in pf.DATE_FIELDS
            desired = pf.parse_date(rec.get(field)) if is_date else rec.get(field)
            if field == "value" and desired == "":
                desired = None
            cell = ws.cell(row, c)
            if is_new_row:
                # style the brand-new cell from the template row, then set format
                if template_row is not None:
                    cell._style = copy(ws.cell(template_row, c)._style)
                if is_date:
                    cell.number_format = DATE_FMT
                elif field == "value":
                    cell.number_format = VALUE_FMT
            if not _same(cell.value, desired, is_date):
                cell.value = desired
                changed += 1
        if is_new_row and template_row is not None:
            rd = ws.row_dimensions
            if template_row in rd and rd[template_row].height:
                rd[row].height = rd[template_row].height

    # clear any leftover data rows below the feed (feed shrank)
    for row in range(pf.FIRST_DATA_ROW + len(records), cur_last + 1):
        for c in range(1, pf.LAST_COL + 1):
            if ws.cell(row, c).value not in (None, ""):
                ws.cell(row, c).value = None
                changed += 1

    after_formulas = pf.formula_set(wb)
    if before_formulas != after_formulas:
        diff = before_formulas ^ after_formulas
        print("ABORT: formula set changed — refusing to save. Delta:", sorted(diff)[:20])
        return 2

    if changed == 0 and not assignments:
        print(f"Pipeline already in sync with feed ({len(records)} rows). No write.")
        return 0

    wb.save(wb_path)
    if assignments:
        pf.dump_feed(feed_path, records)  # persist frozen id assignments
    print(f"Synced {len(records)} Pipeline rows ({changed} cell change(s)) -> {wb_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
