# Changelog

All notable changes to the VBX Command Center are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added — Two staffing-vendor screenings (2026-07-08)
- `Screenings` sheet gains rows #62–#63 (screen date 7/7/2026), both tied to the
  CBO Sentry BPA (RFQ1815037) J4 LCAT sourcing lane:
  - **#62 — NDS Ventures, LLC dba Artemis HCM** (Nick Schutt, CEO). GovCon
    staffing/recruiting supplier evaluated for the J8/J4 key-personnel gap.
    Disposition per screen memo: CONDITIONAL ENGAGE (staff-aug subcontract
    preferred; hourly rate, federal subcontract vehicle, and TES consent are
    gating). No NDA on file (commercial MCSA channel).
  - **#63 — Zachary Piper Solutions, LLC** (Dave Ambrose, Sales Director).
    Cleared-staffing supplier; two-path structure decision (staffing MSA vs.
    lower-tier delivery subcontract). Disposition: HOLD MSA signature, pursue
    subcontract terms in parallel. NDA executed 7/5/2026 (already on the `NDAs`
    sheet, #21).
- Both rows classified `PENDING` (styled pill already supported by the
  dashboard) to reflect the open structure/rate decision on each.
- Recalc validated: 0 formula errors across 254 formulas. Screenings
  trailing-window metrics are unaffected (As-Of 6/8/2026 precedes the 7/7 screens).

### Changed — Vendor SheetJS same-origin (2026-07-08)
- The dashboard now loads SheetJS from `dashboard/vendor/xlsx.full.min.js`
  (served same-origin) instead of `cdn.sheetjs.com`. That CDN is Cloudflare-
  gated and is blocked on some viewer networks, which left the published
  leadership dashboard showing `XLSX is not defined` / "Live feed unavailable"
  with every KPI at `$0`. Serving the parser same-origin removes the last
  third-party runtime dependency (only Google Fonts remains, and it degrades
  gracefully to the fallback stack).
- Vendored build is SheetJS **0.18.5** — the last version published to npm /
  the public GitHub mirror; 0.20.0 is distributed only from the Cloudflare-
  gated origin and is not self-hostable. The dashboard uses only
  `XLSX.read(data, { type:'array', cellDates:true })`, whose behavior is
  identical across these versions.
- `.github/workflows/pages.yml` now copies `dashboard/vendor/` into the
  published `_site/vendor/` and re-publishes when the vendor file changes.
- Verified end-to-end in a headless browser against the published `_site`
  layout: `XLSX.version` resolves to 0.18.5, the workbook auto-loads
  ("Live · updated"), and all KPI cards populate (Revenue $68,500, NDAs 19,
  Pipeline $4.0M, Awarded TCV $2.0M).

### Changed — NDA / Screening contact mapping (2026-07-08)
- Filled the four blank partner contacts (previously shown as `–` in the
  **Executed NDAs** drill-down) in `VBX_Command_Center_v1.1.xlsx`:
  - Grit Government Solutions → Frank Culmone
  - Novarens Systems → Reginald Phillippes
  - FortunaBMC → Alice Parenti
  - Invicta Solutions Group (ISG) → Thomas Radcliffe
- Applied the same mappings to the matching rows on the **Screenings**
  sheet (Primary Contact column) so the entity → contact link stays
  consistent across sheets. Contact is a display-only column — no
  `Metrics_Period` formula depends on it, and the workbook formula count
  is unchanged (254).

### Added — Dashboard: Wins & Awards drill-down (2026-07-08)
- The two **Wins & Awards** summary cards (**Awards Won (#)** and
  **Awarded TCV ($)**) are now **click-to-drill**, matching the Financial
  and Operations KPI cards. Each opens a new `awards` drill-down modal
  titled *Wins & Awards — Award Detail*.
- The drill presents a **summary strip** (Awards Won · Total Awarded TCV ·
  Average Award · Largest Award · % of Y1 ARR Target), the **full award
  ledger** (ID · Opportunity · Client · NAICS · Award Date · TCV · Notes,
  most-recent-first), and a footer reconciling awarded TCV against the
  Year-1 ARR target. Empty state handled when no awards exist.
- Cards use the existing `attachDrillHandlers`/`openDrill` machinery — no
  new dependencies, fonts, or colors; award counting stays stage-based and
  ungated by `As_Of_Date`, consistent with the panel. Verified end-to-end
  headlessly (Chromium): both cards clickable, modal renders 5 stat blocks
  and the awarded row only, closes on Escape.

### Added — Dashboard: Wins & Awards panel (2026-07-08)
- New **Wins & Awards** band on the HTML dashboard (between Operations and
  BD Cadence) so a won opportunity is visible instead of silently dropping
  out of the pipeline once marked *Awarded*. Two teal summary cards —
  **Awards Won (#)** and **Awarded TCV ($)** — plus an **award ledger**
  table (Award · Stage · Award Date · Value), most-recent-first, with each
  opp’s notes on row hover.
- Metrics are **stage-based** (count of `Awarded`-stage opps), mirroring the
  Active Pipeline cards and deliberately **not** gated by `As_Of_Date`, so a
  win stays visible even when the snapshot date predates the award (the
  Montana award dated 06/29/26 shows at the 06/08/26 as-of).
- **Workbook (`Dashboard` sheet):** added matching formulas to the OPERATIONS
  band to preserve the workbook→HTML invariant —
  `G12 =COUNTIF(Pipeline!E5:E1000,"Awarded")` and
  `H12 =SUMIF(Pipeline!E5:E1000,"Awarded",Pipeline!F5:F1000)`, labelled
  *Awards Won (#)* / *Awarded TCV ($)*. Formula count 252 → **254**, 0 errors.
- Verified end-to-end headlessly (Chromium) against the current workbook:
  panel renders **Awards Won 1 / Awarded TCV $2.0M** and the Montana award
  row; Active Pipeline unchanged at 2 / $4.0M. No new fonts, colors, or
  dependencies.

### Removed — Pipeline: pruned 17 opportunities (2026-07-08)
- Removed `Pipeline` rows **OPP-002 through OPP-018** from the workbook
  (`VBX_Command_Center_v1.1.xlsx`): Maryland Statewide Network Services
  (BPM054667) FA4, WA DOH Statewide Rural Health Program (RFP 26-005C),
  RHTP Maryland + Texas state lanes, HRSA Technical Assistance (National
  Backbone), TN Behavioral Telehealth, TN Service Line & Co-Location,
  OPM OIG BRIDGE BPA (RFQ1809527), VA VIPPS (RFQ1809729 Phase II),
  NIH Data Access & Linkage BPA, VHA IHT 2.0, VA.gov Replacement Model
  (DA01), FL & VT RHTP RPM, AR THRIVE, MD Workforce Data Clearinghouse,
  MT RHTP CoE Implementation Vendor, and USAC Enterprise Cybersecurity
  (IT-26-073).
- Surviving `Pipeline` rows keep their original Opp IDs (no renumber, to
  preserve traceability): **OPP-001** Montana AI (Awarded), **OPP-019/020/021**
  (No-Bid), **OPP-022** SENTRY (Capture), and **OPP-023** IHS WebEHRS
  2027-2032 (Submitted — added on `main` via #12; not in the removal list).
  Active Pipeline now = **2 opps / $4.0M** (SENTRY + IHS WebEHRS).
- Dashboard **Active Blockers** trimmed: removed the WA foreign-entity
  registration, eMMA/Maryland (BPM054667), and SOC 2 Type II items — each
  gated only the now-removed pursuits. GSA MAS Refresh 31 and Advocate IT
  teaming blockers retained as standing items.
- No changes to formulas (252 total, 0 errors), column order, header-row
  position, or the workbook→HTML invariant. HTML remains fully
  workbook-driven; KPI cards and the pipeline table recompute from the
  pruned rows.

### Changed — Pipeline: Montana Master AI award (2026-06-29)
- `Pipeline` row **OPP-001** — *Montana AI Products & Services
  (SPB-RFP-2026-0608GW)* moved from **Submitted → Awarded**. Visionblox is
  an apparent successful offeror on **BOTH Track 1 and Track 2** (per the
  State of Montana Notice of Intent to Award); the opp name is broadened to
  *Tracks 1 & 2* accordingly. Stage Date set to **06/29/26** (NOIA received
  from MT DOA State Procurement — Grace Waring, Contracts Officer).
- NOIA only — **not yet an executed contract**; no work may begin until the
  DocuSign contract is signed by all parties, so **no `Active_Projects` row
  yet**. Marking the opp *Awarded* removes its $2M estimate from Active
  Pipeline ($) and drops the Active Pipeline (#), which is the intended
  effect of a win.
- Notes record that **WC, GL ($2M/$2M) and Cyber/Info Security ($6M) COIs
  are secured**, plus the outstanding eMACS awarded-vendor registration and
  10-business-day insurance-doc deadline.
- No changes to formulas (252 total, 0 errors), column order, or the
  workbook→HTML invariant.

### Added — Pipeline: SENTRY pursuit (TES x VBX) (2026-06-27)
- New `Pipeline` row **OPP-022** — *SENTRY (CB26-RFQ0012) — CBO IT Support
  BPA, SMA 2 Cloud Service Support (J4 + J5)*. Customer: Congressional
  Budget Office. Stage: **Capture**. Teaming: TES (prime) x VBX (sub),
  with VBX quoting SMA 2 LCATs — **J4 Microsoft Cloud Engineering SME**
  and **J5 Full Stack Developer**. 5-yr BPA under GSA IT Schedule
  **SIN 54151S**, PoP 08/15/26–08/14/31. Questions due 06/18/26; quote
  due **07/07/26 5pm ET** to OAM@cbo.gov. Public Trust Tier 2 (Capitol
  Police). Remote w/ on-site option at Ford House Office Building, DC.
  VBX-share est. $4M (2 FTE × 5yr). Capture owner: Khaalis Wooden.
- No changes to NDAs/Agreements/Screenings — TES is already on file
  (NDA #10, PRIORITY classification).

### Changed — Workbook bumped to v1.1 (2026-06-09)
- Refreshed leadership workbook to `VBX_Command_Center_v1.1.xlsx`:
  rebuilt `Pipeline` (20 active opps centered on HRSA / VA / RHTP / USAC tracks),
  added screenings rows 57–62 (BAC, NCP, et al.) and one new partner meeting,
  rolled `As_Of_Date` forward to 2026-06-08 (also a `SUMIFS` criterion reorder
  on `Dashboard!D12` — same logic, no math impact)
- Dashboard `REMOTE.url` and as-of-date control retargeted at the v1.1 file
- `.github/workflows/pages.yml` trigger paths + publish step retargeted at the
  v1.1 file (still served as same-origin `VBX_Command_Center_v1.1.xlsx`)
- HTML parsing logic unchanged — no intel duplicated into the dashboard

### Added — Live auto-updating leadership dashboard (owner-authorized 2026-06-05)
- Dashboard now **auto-fetches the workbook** from a same-origin `REMOTE.url`
  on load and **re-polls every 5 min** (cache-busted), so internal leadership
  open one link and never re-upload. Manual upload is retained as a fallback,
  plus a **↻ Refresh** button for on-demand reloads. Reuses `parseWorkbook` /
  `renderAll` unchanged — parser parity verified (11 metrics, 0 drift)
- `.github/workflows/pages.yml` — publishes the dashboard (as `index.html`) +
  its workbook to GitHub Pages. Prefers a sanitized `data/leadership_feed.xlsx`
  when present; otherwise serves the full workbook with a build warning
- **CLAUDE.md Hard Rules #1 and #7 amended** with the dated owner authorization
  scoping this exception to the single leadership workbook + dashboard only

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
