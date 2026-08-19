#!/usr/bin/env python3
"""
export_pipeline_to_feed.py — one-way export: workbook Pipeline sheet -> feed.

Primarily the one-time MIGRATION that seeds data/pipeline_feed.jsonl from the
current committed workbook. Also usable as a rescue tool to rebuild the feed
from the workbook if they ever drift. It never touches the workbook.

Usage:
    python scripts/export_pipeline_to_feed.py \
        [VBX_Command_Center_v1.1.xlsx] [data/pipeline_feed.jsonl]
"""
from __future__ import annotations

import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline_feed as pf  # noqa: E402

WORKBOOK = sys.argv[1] if len(sys.argv) > 1 else "VBX_Command_Center_v1.1.xlsx"
FEED = sys.argv[2] if len(sys.argv) > 2 else "data/pipeline_feed.jsonl"


def main() -> int:
    wb = openpyxl.load_workbook(WORKBOOK, data_only=False)
    ws = wb[pf.SHEET]

    last = pf.HEADER_ROW
    for r in range(pf.FIRST_DATA_ROW, ws.max_row + 1):
        if any(ws.cell(r, c).value not in (None, "") for c in range(1, pf.LAST_COL + 1)):
            last = r

    records: list[dict] = []
    for r in range(pf.FIRST_DATA_ROW, last + 1):
        vals = {name: ws.cell(r, c).value for c, name in enumerate(pf.COLUMNS, 1)}
        opp_id = vals["opp_id"]
        rec = {
            "key": opp_id,  # migrated rows: key == frozen OPP-ID
            "opp_id": opp_id,
            "name": vals["name"],
            "client": vals["client"],
            "naics": vals["naics"],
            "stage": vals["stage"],
            "value": vals["value"] if isinstance(vals["value"], int) else None,
            "date_identified": pf.iso_date(vals["date_identified"]),
            "stage_date": pf.iso_date(vals["stage_date"]),
            "owner": vals["owner"],
            "notes": vals["notes"],
        }
        records.append(rec)

    problems = pf.validate(records)
    if problems:
        print("FEED VALIDATION FAILED:")
        for p in problems:
            print("  -", p)
        return 1

    Path(FEED).parent.mkdir(parents=True, exist_ok=True)
    pf.dump_feed(FEED, records)
    print(f"Exported {len(records)} Pipeline rows -> {FEED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
