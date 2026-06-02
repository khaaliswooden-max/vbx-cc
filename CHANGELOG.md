# Changelog

All notable changes to the VBX Command Center are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed — Brand alignment with visionblox.org (owner-authorized 2026-06-02)
- Dashboard header now uses the **real Visionblox logo mark** (faceted geometric
  "V", inline SVG, pixel-identical to the site asset) and the lowercase
  `visionblox` wordmark in DM Serif Display
- Adopted the public site's **type system**: DM Serif Display (headline figures),
  DM Sans (body), JetBrains Mono (technical labels + tabular data), via Google
  Fonts CDN. Updates CLAUDE.md §4 and Hard Rule #5 (Arial retained as fallback
  and for Excel artifacts)
- Restyled chrome to match the site: `// SECTION` mono headers, mono tabular
  data cells, serif KPI/scenario figures, warm-paper background (`#F5F5F0`),
  gold `UPLOAD WORKBOOK →` CTA, mono badges/pills/controls
- Inline-SVG favicon now uses the real logo mark

### Added
- `scripts/verify_parse.js` — headless verifier (CLAUDE.md §9) that replicates
  the dashboard's `parseWorkbook` + trailing-window math and cross-checks it
  against the workbook's formula-computed `Metrics_Period` (11 metrics, 0 drift)

### Fixed
- Renamed the misnamed `download` file to `.gitignore` so `output/` (real-data
  workbooks) is actually ignored, per Hard Rule #1

### Planned — Phase 2 (target: v1.1.0)
- Stage-transition logging on `Pipeline` sheet (track time-in-stage for funnel velocity)
- Classification change-log on `Screenings` sheet (track partner stage transitions)
- Sparkline chart for trailing-180-day cadence (in addition to T-90d)
- CSV export from any drill-down modal in the dashboard
- Cycle-time slider wired into scenario math (currently informational only)

### Planned — Phase 3 (target: v2.0.0)
- Post-award performance tracking: CPARS, SLA, milestone burn
- Feedback log analytics: sentiment trend, action-item aging
- Multi-year P/L view (once two full years of actuals exist)
- Automated workbook → dashboard sync (eliminate re-upload step)

---

## [1.0.0] — 2026-06-02

Initial release. Combined Phase 0 (workbook system of record) and Phase 1
(HTML presentation layer).

### Added — Phase 0: Workbook
- `scripts/build_command_center.py` — generates the system-of-record workbook
- 12-sheet workbook structure: `Dashboard`, `Targets`, `Metrics_Period`,
  `Revenue_Ledger`, `Expense_Ledger`, `Meetings`, `Pipeline`,
  `Active_Projects`, `Feedback`, `Screenings`, `NDAs`, `Agreements`
- 252 formulas across the workbook, zero validation errors
- Trailing-window metrics engine: WoW (7d), MoM (30d), QoQ (91d), YoY (365d)
- Brand styling: Navy `#232D5A` / Teal `#2EA891` / Gold `#F7B801` / Arial
- Defined-name `As_Of_Date` drives all time-series computation
- Conditional formatting on delta columns (green positive / red negative)
- Classification color-coding on partner screenings
- Income-statement reconciliation: explicit Run-Rate P/L line (–$47,870) and
  Gap to Break-Even line ($47,870) on `Targets` sheet
- Budgeted P/L row on `Metrics_Period` that uses annual expense budget as proxy
  when `Expense_Ledger` is empty

### Added — Phase 1: HTML dashboard
- `dashboard/VBX_Command_Center_Dashboard.html` — single-file dashboard
- Client-side parsing via SheetJS (v0.20.0, CDN)
- Drag-to-upload workbook ingestion
- Adjustable as-of-date control (any historical snapshot)
- 5 financial headline cards + 4 operations headline cards (clickable drill-downs)
- BD Cadence table with 13-week sparklines per KPI row
- Financial Cadence table with parallel actual + budgeted P/L rows
- Pipeline table with color-coded stage pills
- Scenario Mode panel: win rate × Y1 booking % → projected Y1 P/L
- Sensitivity table: Y1 P/L at 5%, 10%, 15%, 20%, 25%, 30%, 40%, 50% win rates
- 8 drill-down modal types: revenue, pipeline, projects, NDAs, agreements,
  meetings, screenings, ARR breakdown, P/L reconciliation
- ESC-to-close, click-outside-to-close on modals
- Federal-ops-command aesthetic: tabular numerics, navy header,
  dense data zones, no glassmorphism

### Added — Seed data (back-filled from existing tracker)
- 56 partner screenings (Apr 1 → Jun 1, 2026)
- 19 executed NDAs
- 2 executed agreements (1 fully populated; 1 partial)
- 5 active pipeline opportunities ($14.5M TCV)
- 10 revenue invoices (HCPSS + First Brands Group, Jan → May 2026)
- 55 meetings (AG Grace weekly syncs + 36 partner discovery/intro/sync)

### Documentation
- README, LICENSE, CHANGELOG, CLAUDE.md, SECURITY.md, .gitignore
- `data/README.md` — input format specification

### Notes
- `Expense_Ledger` is intentionally empty in seed data — actuals must be
  populated by operator. Budgeted P/L row uses annual budget proxy until then.
- `Active_Projects` and `Feedback` sheets are clean-slate by design.

---

[Unreleased]: https://github.com/visionblox-internal/vbx-command-center/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/visionblox-internal/vbx-command-center/releases/tag/v1.0.0
