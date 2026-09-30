#!/usr/bin/env python3
"""
organize_workbook.py — make the Command Center workbook easy to operate by hand.

WHY THIS EXISTS
The workbook is the system of record (CLAUDE.md §2), but 15 unlabeled tabs with
free-typed categories are easy to get wrong: one misspelled Status or one date
typed as text silently drops a row from the KPIs. This script adds the
operator-facing layer IN PLACE, without touching any data, header or column:

  1. Start_Here  — a home tab: color key, daily routine, one clickable link per
                   tab with what goes there, and what the public site publishes
                   (derived from build_leadership_feed.py, so it cannot drift).
  2. Tab order + color — grouped by what the operator does on each tab.
  3. Dropdowns + date/amount checks on the hand-entered input columns.
  4. Dashboard hygiene — the Active Blockers list is copied from the HTML
     dashboard's .blockers-list (the authoritative set, Hard Rule #10), and the
     expense-proxy note reads the budget from Targets!C6 instead of a stale number.
  5. Opportunity_Detail banner — rewritten from pipeline_feed.DETAIL_BANNER.

THIS FILE HOLDS NO DATA (Hard Rule #1). Dropdown lists are category vocabularies
taken from each sheet's own banner row, never partner names.

RULES THE SCRIPT ENFORCES
  * Idempotent: a re-run rebuilds Start_Here and replaces only its own dropdowns.
  * Every row-4 header and every data cell (row 5+) on every data sheet is
    unchanged, or nothing is saved.
  * The formula set is unchanged except Dashboard!B30 (the expense-proxy note),
    or nothing is saved.
  * A strict ("stop") dropdown must already accept every value in its column,
    or nothing is saved.
  * Pipeline and Opportunity_Detail get no dropdowns: the feed sync rewrites
    them (CLAUDE.md §7 Workflow F).

    python scripts/organize_workbook.py [--check] [--workbook PATH]

  --check   print what would change and write nothing.
"""
from __future__ import annotations

import argparse
import copy
import html
import math
import re
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.hyperlink import Hyperlink

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_leadership_feed as feed  # noqa: E402
import pipeline_feed as pf  # noqa: E402

# === CONSTANTS === #
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKBOOK = ROOT / "VBX_Command_Center_v1.1.xlsx"
DASHBOARD_HTML = ROOT / "dashboard" / "VBX_Command_Center_Dashboard.html"
HOME = "Start_Here"
STYLE_SOURCE = "Actions"          # title / banner / header styling is copied from here
LAST_ROW = 1000                   # matches the Pipeline!E5:E1000 ranges on Dashboard

NAVY, TEAL, GOLD, AMBER = "FF232D5A", "FF2EA891", "FFF7B801", "FFF59E0B"
WHITE, BLACK = "FFFFFFFF", "FF000000"

# Color key: (tab color, short label, meaning, label text color)
GROUPS = {
    "look":     (NAVY,  "Look here",      "Results. Read these; the only cell you type in is the As-of Date (Dashboard!C4).", WHITE),
    "type":     (GOLD,  "You type here",  "Add one row per event, starting at the first empty row under the headers.", BLACK),
    "auto":     (TEAL,  "Automatic",      "Filled by formulas or by the Pipeline feed sync. Do not type here; edits are overwritten.", WHITE),
    "internal": (AMBER, "Internal only",  "Never shared. Removed from the public copy before publishing.", BLACK),
}

# Tab order = the order Start_Here lists them. (sheet, group, what goes here, rules)
TABS = [
    ("Dashboard", "look",
     "Headline numbers, BD cadence vs target, financial cadence, active blockers.",
     "Set C4 (As-of Date) to today before reading. Every trailing window counts back from it."),
    ("Actions", "type",
     "Your to-do list: action, owner, deadline, success condition, status.",
     "Add a row when a task is assigned; update Status as it moves. Published in full: "
     "cite inbound firms by IN- ID, never by name."),
    ("Meetings", "type",
     "Calls and meetings that have already happened.",
     "Add the row AFTER the meeting happens, not when it is scheduled. Every dated row counts."),
    ("Screenings", "type",
     "Partner firms you have screened, with tier (PRIORITY / BENCH / WATCHLIST / FILED / PENDING).",
     "Add a firm only once it is actually screened. Column E is the date the KPIs count."),
    ("NDAs", "type",
     "Non-disclosure agreements with partners.",
     "Enter the Date (column D) only when the NDA is fully executed. A dated row counts as executed."),
    ("Agreements", "type",
     "Teaming, commission and partnership agreements.",
     "Enter the Date (column D) when the agreement is executed."),
    ("Inbound_Leads", "internal",
     "Unscreened inbound firms and their scheduled calls.",
     "Loaded by scripts/upsert_inbound_leads.py. You may edit Status, NDA status, next step. "
     "Classification / Score / Verified stay empty until the firm is screened."),
    ("Pipeline", "auto",
     "Every opportunity: stage, value, dates, capture owner.",
     "Do not type here. Edit data/pipeline_feed.jsonl; the sync job on main rewrites this tab."),
    ("Opportunity_Detail", "auto",
     "BD posture and technical scope for each Pipeline opportunity.",
     "Do not type here (same feed as Pipeline). PUBLIC: write every cell as if a competitor reads it."),
    ("Active_Projects", "type",
     "Awarded contracts being delivered.",
     "Add a row when a contract is awarded. Status 'Active' is what the Dashboard counts."),
    ("Revenue_Ledger", "type",
     "Invoices issued and payments received.",
     "Add a row per invoice. Amount Invoiced drives every revenue metric."),
    ("Expense_Ledger", "type",
     "Money spent, by income-statement category.",
     "Add a row per expense. Until this has rows, Net P/L uses the budget as a proxy."),
    ("Feedback", "type",
     "Client, partner and internal feedback.",
     "Add a row when feedback arrives."),
    ("Targets", "type",
     "Goals: ARR target, expense budget, weekly BD cadence targets.",
     "Rarely. Change BLUE numbers only; black cells are formulas."),
    ("Metrics_Period", "auto",
     "The calculation engine behind the Dashboard (trailing 7/30/91-day windows).",
     "Never type here."),
]

ROUTINE = [
    "Open Dashboard and set the As-of Date (cell C4) to today. Every number recalculates to that date.",
    "Log what happened today on the GOLD tabs: one row per meeting, screening, NDA, invoice or expense.",
    "In category columns, click the cell and use the dropdown arrow instead of typing.",
    "Type dates as mm/dd/yyyy. A date typed as text is invisible to the KPI counts, so Excel rejects it.",
    "Update Status on Actions, then save. The HTML dashboard and the leadership site read this file.",
]

TIPS = [
    ("Next / previous tab", "Windows: Ctrl+PgDn / Ctrl+PgUp.   Mac: Option+→ / Option+←."),
    ("List every tab", "Right-click the small arrows at the bottom-left of the window."),
    ("Strict lists", "Partner tiers and Project Status only accept list values; Excel refuses anything else."),
    ("Soft lists", "Other dropdowns warn you. Choose Yes only when you truly need a new category."),
]

# === DROPDOWNS === #
TIERS = ["PRIORITY", "BENCH", "WATCHLIST", "FILED", "PENDING"]
DATE_MIN, DATE_MAX = "DATE(2020,1,1)", "DATE(2035,12,31)"

# (sheet, column, kind, values, style). kind: list | date | amount.
# Lists come from each sheet's own row-2 banner, plus every value already in use.
VALIDATIONS = [
    ("Actions", "D", "date", None, "warning"),
    ("Actions", "F", "list", ["Not started", "Open", "In Progress", "Needs Khaalis decision",
                              "OVERDUE", "Done"], "warning"),
    ("Meetings", "A", "date", None, "stop"),
    ("Meetings", "D", "list", ["Intro", "Discovery", "Exploratory", "Sync", "Capture",
                               "Customer", "Post-Award", "Internal"], "warning"),
    ("Screenings", "E", "date", None, "stop"),
    ("Screenings", "F", "date", None, "stop"),
    ("Screenings", "H", "list", TIERS, "stop"),
    ("NDAs", "D", "date", None, "stop"),
    ("NDAs", "F", "list", ["Executed",
                           "Signed by VBX — awaiting countersignature (not executed)"], "warning"),
    ("NDAs", "G", "list", TIERS, "stop"),
    ("Agreements", "D", "date", None, "stop"),
    ("Agreements", "E", "list", ["BD Commission Agreement", "BD Commission Agreement — Template",
                                 "Teaming Agreement", "Partnership Agreement"], "warning"),
    ("Agreements", "G", "list", ["Executed", "Template on File"], "warning"),
    ("Inbound_Leads", "N", "list", ["Replied", "Call Scheduled", "Parked"], "warning"),
    ("Inbound_Leads", "O", "date", None, "warning"),
    ("Inbound_Leads", "R", "list", ["Not sent", "Sent", "Executed"], "warning"),
    ("Inbound_Leads", "W", "list", TIERS, "stop"),
    ("Active_Projects", "E", "amount", None, "warning"),
    ("Active_Projects", "F", "date", None, "stop"),
    ("Active_Projects", "G", "date", None, "stop"),
    ("Active_Projects", "H", "list", ["Active", "Paused", "Complete", "Closeout"], "stop"),
    ("Revenue_Ledger", "A", "date", None, "stop"),
    ("Revenue_Ledger", "E", "amount", None, "warning"),
    ("Revenue_Ledger", "F", "amount", None, "warning"),
    ("Revenue_Ledger", "G", "date", None, "stop"),
    ("Expense_Ledger", "A", "date", None, "stop"),
    ("Expense_Ledger", "B", "list", ["Payroll", "Office", "Marketing & BD", "Travel", "Software",
                                     "Taxes", "Miscellaneous"], "warning"),
    ("Expense_Ledger", "D", "amount", None, "warning"),
    ("Feedback", "A", "date", None, "stop"),
    ("Feedback", "B", "list", ["Internal", "External"], "warning"),
    ("Feedback", "D", "list", ["CPARS", "Survey", "Email", "Verbal", "Slack"], "warning"),
]

# === DASHBOARD HYGIENE === #
BLOCKER_FIRST_ROW, BLOCKER_LAST_ROW = 33, 37   # Dashboard!B33:B37, one merged row each
PROXY_NOTE_CELL = "B30"
PROXY_NOTE = (
    '=IF(COUNT(Expense_Ledger!D5:D1000)=0,"  ⚠  Net P/L (actuals-only) is partial: '
    'Expense_Ledger has no entries yet. The ""actual rev vs budget exp"" row above uses the '
    'pro-rated annual budget ("&TEXT(Targets!C6,"$#,##0")&" ÷ 365) as an expense proxy '
    'until you log actual expenses.","")'
)


# === HELPERS === #
def copy_style(dst, src) -> None:
    dst.font, dst.fill = copy.copy(src.font), copy.copy(src.fill)
    dst.alignment, dst.border = copy.copy(src.alignment), copy.copy(src.border)


def fill(rgb: str) -> PatternFill:
    return PatternFill("solid", fgColor=rgb)


def lines_needed(text: str, width_chars: float) -> int:
    return max(1, math.ceil(len(text) / max(width_chars * 1.15, 1)))


def html_blockers() -> list[str]:
    """The Active Blockers list from the HTML dashboard — the authoritative set."""
    src = DASHBOARD_HTML.read_text(encoding="utf-8")
    block = re.search(r'<div class="blockers-list">(.*?)</div>\s*</section>', src, re.S)
    if not block:
        raise SystemExit("ABORT: .blockers-list not found in the HTML dashboard.")
    items = re.findall(r'<div class="blocker-item">(.*?)</div>', block.group(1), re.S)
    return [html.unescape(re.sub(r"\s+", " ", i)).strip() for i in items]


def snapshot(wb) -> dict[str, object]:
    """Every header (row 4) and data cell (row 5+) on every sheet except the home tab
    and the two cells this script owns on Dashboard."""
    owned = {f"Dashboard!{PROXY_NOTE_CELL}"} | {
        f"Dashboard!B{r}" for r in range(BLOCKER_FIRST_ROW, BLOCKER_LAST_ROW + 1)}
    out = {}
    for ws in wb.worksheets:
        if ws.title == HOME:
            continue
        for row in ws.iter_rows(min_row=pf.HEADER_ROW):
            for c in row:
                key = f"{ws.title}!{c.coordinate}"
                if c.value is not None and key not in owned:
                    out[key] = c.value
    return out


# === 1. START_HERE === #
def build_home(wb) -> None:
    if HOME in wb.sheetnames:
        del wb[HOME]
    ws = wb.create_sheet(HOME, 0)
    ws.sheet_view.showGridLines = False
    style = wb[STYLE_SOURCE]
    widths = {"A": 2, "B": 24, "C": 17, "D": 46, "E": 72}
    for letter, width in widths.items():
        ws.column_dimensions[letter].width = width
    wide = widths["C"] + widths["D"] + widths["E"]

    def section(row: int, text: str) -> None:
        c = ws.cell(row, 2, text)
        c.font = Font(name="Arial", size=12, bold=True, color=NAVY)
        ws.row_dimensions[row].height = 20

    def body(row: int, col: int, text: str, bold=False, color=BLACK, merge_to=None) -> None:
        c = ws.cell(row, col, text)
        c.font = Font(name="Arial", size=10, bold=bold, color=color)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if merge_to:
            ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=merge_to)

    # Rows 1–2: brand title + banner, copied from the input sheets' house style
    ws.merge_cells("A1:E1")
    ws.merge_cells("A2:E2")
    ws["A1"] = "  START HERE  —  VBX Command Center"
    ws["A2"] = "  Click any tab name below to jump to it. The tab color tells you what to do there."
    copy_style(ws["A1"], style["A1"])
    copy_style(ws["A2"], style["A2"])
    ws.row_dimensions[1].height = style.row_dimensions[1].height
    ws.row_dimensions[2].height = style.row_dimensions[2].height

    row = 4
    section(row, "COLOR KEY")
    for key in ("look", "type", "auto", "internal"):
        row += 1
        rgb, label, meaning, text_rgb = GROUPS[key]
        c = ws.cell(row, 2, label)
        c.fill, c.font = fill(rgb), Font(name="Arial", size=10, bold=True, color=text_rgb)
        c.alignment = Alignment(horizontal="center", vertical="center")
        body(row, 3, meaning, merge_to=5)
        ws.row_dimensions[row].height = 18

    row += 2
    section(row, "DAILY ROUTINE")
    for n, step in enumerate(ROUTINE, 1):
        row += 1
        c = ws.cell(row, 2, n)
        c.font = Font(name="Arial", size=11, bold=True, color=NAVY)
        c.alignment = Alignment(horizontal="center", vertical="top")
        body(row, 3, step, merge_to=5)
        ws.row_dimensions[row].height = 15 * lines_needed(step, wide) + 3

    row += 2
    section(row, "WHERE EVERYTHING GOES  —  click a tab name to jump there")
    row += 1
    for col, head in enumerate(("Tab", "Color", "What goes here", "When to add a row / rules"), 2):
        copy_style(ws.cell(row, col, head), style.cell(pf.HEADER_ROW, 2))
    ws.row_dimensions[row].height = 22
    for sheet, group, what, rules in TABS:
        if sheet not in wb.sheetnames:
            continue
        row += 1
        rgb, label, _, text_rgb = GROUPS[group]
        link = ws.cell(row, 2, sheet)
        link.hyperlink = Hyperlink(ref=link.coordinate, location=f"'{sheet}'!A1")
        link.font = Font(name="Arial", size=10, bold=True, underline="single", color=NAVY)
        link.alignment = Alignment(vertical="top")
        tag = ws.cell(row, 3, label)
        tag.fill, tag.font = fill(rgb), Font(name="Arial", size=9, bold=True, color=text_rgb)
        tag.alignment = Alignment(horizontal="center", vertical="top")
        body(row, 4, what)
        body(row, 5, rules)
        ws.row_dimensions[row].height = 13 * max(lines_needed(what, widths["D"]),
                                                  lines_needed(rules, widths["E"])) + 4

    row += 2
    section(row, "WHAT THE PUBLIC LEADERSHIP SITE SHOWS  (GitHub Pages is public and search-indexable)")
    for label, text in publication_lines(wb):
        row += 1
        body(row, 2, label, bold=True, color=NAVY)
        body(row, 3, text, merge_to=5)
        ws.row_dimensions[row].height = 13 * lines_needed(text, wide) + 4

    row += 2
    section(row, "TIPS")
    for label, text in TIPS:
        row += 1
        body(row, 2, label, bold=True, color=NAVY)
        body(row, 3, text, merge_to=5)


def publication_lines(wb) -> list[tuple[str, str]]:
    """Plain-English publish policy, read from build_leadership_feed.py's own tables."""
    stripped = [s for s in feed.STRIP_SHEETS if s in wb.sheetnames]
    partial = []
    for sheet, allowed in feed.PUBLISH_COLUMNS.items():
        if sheet not in wb.sheetnames:
            continue
        ws = wb[sheet]
        hidden = [str(ws.cell(pf.HEADER_ROW, c).value) for c in range(1, ws.max_column + 1)
                  if c not in allowed and ws.cell(pf.HEADER_ROW, c).value]
        if hidden:
            partial.append(f"{sheet} (hides {', '.join(hidden)})")
    listed = set(stripped) | {p.split(" ")[0] for p in partial}
    full = [s for s, _, _, _ in TABS if s in wb.sheetnames and s not in listed]
    full += [s for s in wb.sheetnames if s not in listed and s not in full]
    return [
        ("Never published", ", ".join(stripped) + "."),
        ("Published, some columns hidden", "; ".join(partial) + "."),
        ("Published in full", ", ".join(full) + "."),
    ]


# === 2. TAB ORDER + COLOR === #
def order_tabs(wb) -> list[str]:
    planned = [HOME] + [s for s, _, _, _ in TABS if s in wb.sheetnames]
    extra = [s for s in wb.sheetnames if s not in planned]
    wb._sheets = [wb[s] for s in planned + extra]
    groups = {s: g for s, g, _, _ in TABS}
    for ws in wb.worksheets:
        group = "look" if ws.title == HOME else groups.get(ws.title)
        if group:
            ws.sheet_properties.tabColor = GROUPS[group][0]
        ws.sheet_view.tabSelected = ws.title == HOME   # >1 selected = grouped-edit mode
    wb.active = 0
    return extra


# === 3. DROPDOWNS === #
def add_validations(wb) -> list[str]:
    notes = []
    for sheet, col, kind, values, style in VALIDATIONS:
        if sheet not in wb.sheetnames:
            continue
        ws = wb[sheet]
        header = ws[f"{col}{pf.HEADER_ROW}"].value
        rng = f"{col}{pf.FIRST_DATA_ROW}:{col}{LAST_ROW}"
        ws.data_validations.dataValidation = [
            dv for dv in ws.data_validations.dataValidation if str(dv.sqref) != rng]
        if kind == "list":
            formula = '"' + ",".join(values) + '"'
            if len(formula) > 257 or any("," in v for v in values):
                raise SystemExit(f"ABORT: {sheet}!{col} list too long or contains a comma.")
            present = {str(ws[f"{col}{r}"].value) for r in range(pf.FIRST_DATA_ROW, ws.max_row + 1)
                       if ws[f"{col}{r}"].value not in (None, "")}
            stray = sorted(present - set(values))
            if stray and style == "stop":
                raise SystemExit(f"ABORT: strict list on {sheet}!{col} rejects values in use: {stray}")
            if stray:
                notes.append(f"{sheet}!{col} ({header}): {len(stray)} existing value(s) off-list "
                             "— kept; Excel warns only when that cell is edited")
            dv = DataValidation(type="list", formula1=formula, allow_blank=True)
            dv.promptTitle, dv.prompt = "Pick from the list", "Click the arrow to choose."
            dv.errorTitle = "Not on the list"
            dv.error = ("Choose a value from the dropdown." if style == "stop" else
                        "This value is not on the list. Choose Yes only if you need a new category.")
        elif kind == "date":
            dv = DataValidation(type="date", operator="between", formula1=DATE_MIN,
                                formula2=DATE_MAX, allow_blank=True)
            dv.promptTitle, dv.prompt = "Date", "Type the date as mm/dd/yyyy."
            dv.errorTitle = "Not a date"
            dv.error = ("Type a real date as mm/dd/yyyy (2020–2035). Text dates are invisible "
                        "to the KPI counts.")
        else:
            dv = DataValidation(type="decimal", operator="greaterThanOrEqual", formula1="0",
                                allow_blank=True)
            dv.promptTitle, dv.prompt = "Amount", "Dollars, numbers only (no $ sign needed)."
            dv.errorTitle = "Not an amount"
            dv.error = "Enter a number of dollars, 0 or more."
        dv.errorStyle = style
        dv.showErrorMessage = dv.showInputMessage = True
        dv.add(rng)
        ws.add_data_validation(dv)
    return notes


# === 4–5. DASHBOARD + BANNER HYGIENE === #
def fix_dashboard(wb) -> list[str]:
    ws = wb["Dashboard"]
    blockers = html_blockers()
    slots = BLOCKER_LAST_ROW - BLOCKER_FIRST_ROW + 1
    if len(blockers) > slots:
        raise SystemExit(f"ABORT: {len(blockers)} HTML blockers but only {slots} Dashboard rows.")
    for i, r in enumerate(range(BLOCKER_FIRST_ROW, BLOCKER_LAST_ROW + 1)):
        ws[f"B{r}"] = f"• {blockers[i]}" if i < len(blockers) else None
    ws[PROXY_NOTE_CELL] = PROXY_NOTE
    if pf.DETAIL_SHEET in wb.sheetnames:
        wb[pf.DETAIL_SHEET]["A2"] = pf.DETAIL_BANNER
    return blockers


# === MAIN === #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    ap.add_argument("--check", action="store_true", help="dry run; write nothing")
    args = ap.parse_args()

    wb = openpyxl.load_workbook(args.workbook)
    formulas_before, data_before = pf.formula_set(wb), snapshot(wb)

    blockers = fix_dashboard(wb)
    notes = add_validations(wb)
    build_home(wb)
    extra = order_tabs(wb)

    if pf.formula_set(wb) != formulas_before | {f"Dashboard!{PROXY_NOTE_CELL}"}:
        raise SystemExit("ABORT: formula set changed beyond Dashboard!B30 — nothing saved.")
    if snapshot(wb) != data_before:
        diff = set(snapshot(wb).items()) ^ set(data_before.items())
        raise SystemExit(f"ABORT: header/data cells changed — nothing saved: {sorted(diff)[:5]}")

    print("Tab order:", " → ".join(wb.sheetnames))
    if extra:
        print("  Unplanned tabs kept at the end:", ", ".join(extra))
    print(f"Dropdowns / checks: {sum(1 for v in VALIDATIONS if v[0] in wb.sheetnames)} columns")
    for n in notes:
        print("  note:", n)
    print(f"Dashboard blockers (from HTML): {len(blockers)}")
    print(f"Formulas: {len(pf.formula_set(wb))} (Dashboard!B30 is formula-driven)")
    print("Header and data cells: unchanged")
    if args.check:
        print("--check: nothing written.")
        return 0
    wb.save(args.workbook)
    print(f"Saved {args.workbook}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
