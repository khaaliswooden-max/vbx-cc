# VBX Command Center

Operations dashboard for Visionblox LLC business development. Tracks pipeline, partners, NDAs, agreements, meetings, screenings, revenue, expenses, and P/L performance against internal targets — with WoW / MoM / QoQ / YoY trend analysis.

**Status:** Phase 0 + Phase 1 complete (v1.0.0). Phase 2/3 on the roadmap — see [CHANGELOG.md](./CHANGELOG.md).

---

## Architecture

The system has two layers:

| Layer | File | Role |
|---|---|---|
| **System of record** | `output/VBX_Command_Center_v1.xlsx` | All operational data. 12 sheets. 252 formulas. Updated daily via direct entry. |
| **Presentation layer** | `dashboard/VBX_Command_Center_Dashboard.html` | Interactive viewer. Parses workbook client-side via SheetJS. Drill-downs, sparklines, scenario mode. |

The workbook is the truth. The HTML reads it and renders it. Never invert this relationship — never let the dashboard hold state that isn't in the workbook.

---

## Quick start

### Prerequisites
- Python 3.10+ with `openpyxl` (for the workbook builder)
- A modern browser (Chrome, Edge, Safari, Firefox — for the dashboard)
- Microsoft Excel or LibreOffice (for daily data entry)

### Install Python dependencies
```bash
pip install -r requirements.txt
```

### Build the workbook
```bash
python scripts/build_command_center.py
```
Output lands in `output/VBX_Command_Center_v1.xlsx`.

### Open the dashboard
Open `dashboard/VBX_Command_Center_Dashboard.html` in any browser. Upload the workbook via the top-right button. The dashboard parses it client-side — nothing leaves the machine.

---

## Daily workflow

1. **Open the workbook** in Excel
2. **Add rows** to whichever input sheets had activity:
   - `Revenue_Ledger` — new invoices issued or paid
   - `Expense_Ledger` — expenses incurred
   - `Meetings` — capture / sync / intro / post-award meetings
   - `Pipeline` — new opportunities or stage changes
   - `Active_Projects` — post-award contract execution
   - `Feedback` — internal/external feedback
   - `Screenings`, `NDAs`, `Agreements` — partner ecosystem activity
3. **Save the workbook**
4. **Open the dashboard** → re-upload the workbook → metrics refresh
5. **Move the "As-of Date"** to view any historical snapshot

---

## Repo structure

```
vbx-command-center/
├── README.md                  ← this file
├── LICENSE                    ← Proprietary / All Rights Reserved
├── CHANGELOG.md               ← version history
├── CLAUDE.md                  ← Claude Code agentic instructions
├── SECURITY.md                ← sensitive data handling
├── .gitignore
├── requirements.txt
├── scripts/
│   └── build_command_center.py    ← workbook generator (Python + openpyxl)
├── dashboard/
│   └── VBX_Command_Center_Dashboard.html   ← single-file HTML viewer
├── data/
│   ├── README.md              ← input format specification
│   └── targets_template.xlsx  ← schema-only template (placeholder values)
└── output/                    ← gitignored; generated workbooks land here
```

---

## KPI inventory

**Financial:** Year-1 ARR target, Revenue Booked YTD, Run-Rate P/L, Gap to Break-Even, Gap to ARR Target
**Operations:** Active Pipeline (#, $), Active Projects, NDAs Executed YTD
**BD Cadence (trailing windows):** Screenings, NDAs, Agreements, Meetings, New Pipeline Opps
**Financial Cadence:** Revenue (actual), Expenses (actual + budgeted), Net P/L (actual + budgeted)
**Scenario Mode:** Win rate × Y1 booking % → projected Y1 P/L

All trailing computations use:
- **WoW:** T-7d vs prior 7d
- **MoM:** T-30d vs prior 30d
- **QoQ:** T-91d vs prior 91d
- **YoY:** T-365d vs prior 365d

---

## Brand standards

Mandatory across all generated artifacts:
- **Colors:** Navy `#232D5A` · Teal `#2EA891` · Gold `#F7B801`
- **Font:** Arial (per VBX visual identity)
- **Logo:** Required on all internal and external documents

Brand drift in any output is a defect. See [CLAUDE.md](./CLAUDE.md) for full design constants.

---

## Confidentiality

This repo contains proprietary BD intelligence: partner names, pipeline values, revenue figures, NDA register, and indirect references to internal IP frameworks. **It must remain private.** Public release of any file requires written authorization from the Director of Enterprise Capture & Compliance.

See [SECURITY.md](./SECURITY.md) for handling rules.

---

## License

Proprietary. All rights reserved. See [LICENSE](./LICENSE).

---

## Contact

**Director of Enterprise Capture & Compliance**
Khaalis Wooden, MBA
khaalis.wooden@visionblox.com
(256) 988-1130

Visionblox LLC · 2570 N. First Street, San Jose, CA 95131
CAGE 9Z4X2 · UEI H4X2Z7R9E3E3 · GSA MAS SIN 54151HEAL
