# Changelog

All notable changes to the VBX Command Center are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed — CMS ICAT RFI 270196 pursuit updated: VBX cleared for submission (2026-08-19)
Updated the ICAT pursuit line (`OPP-031`) in `data/pipeline_feed.jsonl` to reflect the
`STATE AS OF 8/18 — VBX representation CLEARED for submission`. Health **AMBER →
trending GREEN** (one hard gate open). Team structure confirmed: **Aurelus Solutions
(prime) / CAGAIL LLC (sub) / Visionblox (sub)**.

- **Name corrected:** "Independent Coding Audit Tool" → **"Intelligent Coding Assistance
  Tool"** (correct ICAT expansion).
- **Prime resolved:** the 8/13 "Shan" placeholder resolved to **Aurelus Solutions**
  (screened/cleared by KW 8/15) — NOT Cadence / Shaneiqua Johnson; FILED contingency
  **closed**.
- **State captured:** NDA executed 8/16; response redlined 8/17 (6 tracked VBX edits);
  VBX representation cleared 8/18 with **zero residual false VBX claims** (GSA MAS/SIN
  54151HEAL struck, "HITRUST-audited" → "assessor-on-staff", CMS/FEMA mis-attribution
  fixed).
- **Open hard gate:** 3 signed COI attestations (Aurelus, CAGAIL, VBX), target Tue 8/19
  EOD; solo fallback preserved (5.60, Credible).
- **Corrections to prior CC entry:** deadline **Thu 8/20** 10:00 ET (not Wed);
  per-question limit **3,000 chars** (not 2,000); FSIPAP 8/19 → ICAT 8/20 **sequential**,
  not stacked.
- **Branded record produced** (`ICAT_Pursuit_Status_270196_20260819.docx` + `.pdf`) via
  the VBX docx pipeline (docx-js → validate.py → border patch → repack → re-validate →
  PDF → preview). Delivered to the owner **out-of-repo** — it carries teaming-partner and
  executed-NDA detail prohibited from the repo by Hard Rule #1; only the Pipeline-feed
  note (permitted under the 2026-08-19 feed exception) is committed.

### Added — Text-mergeable Pipeline feed + deterministic sync (2026-08-19)
Introduced `data/pipeline_feed.jsonl` as the source of record for the `Pipeline`
sheet, to end binary-workbook merge conflicts and OPP-ID collisions when multiple
branches add pipeline rows concurrently. The workbook remains the system of record
the dashboard reads (Hard Rule #4 invariant intact); the feed is the merge-safe
input source, synced into the workbook at a single serialization point (`main`).

- **`data/pipeline_feed.jsonl`** — one JSON object per opportunity, one physical
  line each, so git auto-merges concurrent appends. Owner-authorized addition to
  the Rule #1 real-data exception (2026-08-19, Khaalis Wooden); not published.
  Seeded losslessly from the current 25 Pipeline rows (round-trip verified: 0 cell
  diffs).
- **`scripts/pipeline_feed.py`** — schema, loader/dumper, deterministic OPP-ID
  assignment, and validation helpers.
- **`scripts/sync_pipeline_from_feed.py`** — feed → workbook Pipeline rows.
  Value-diff writer (idempotent), assigns/freezes OPP-IDs, and **asserts the
  254-formula set is unchanged** before saving. `--check` mode validates only.
- **`scripts/export_pipeline_to_feed.py`** — one-way workbook → feed rebuild
  (migration + drift rescue).
- **`.github/workflows/sync-pipeline.yml`** — validates the feed on PRs; on push to
  `main` regenerates the workbook from the feed and commits it back (loop-safe:
  `GITHUB_TOKEN` pushes don't re-trigger CI, sync is idempotent, `[skip ci]`).
- **`docs/HOW_TO_USE_Pipeline_Feed.md`** and CLAUDE.md **Workflow F** document the
  add-an-opportunity flow.

### Added — DoWEA/DoDEA Data, Analytics & AI pursuit logged as WATCH (2026-08-19)
Logged the DoWEA/DoDEA Data, Analytics, and AI Modernization Services pursuit
(Solicitation `HE125426RE037`) into the system-of-record workbook as a WATCH item.
SAM status re-verified on 2026-08-19 immediately before logging: `isActive=false`,
`isCanceled=true` (latest notice `e309ee9b147547db8a7020562e4f8acc`, cancelled
2026-08-17). No status flip.

- **Pipeline — 1 new row (OPP-040):**
  - **OPP-040 — DoWEA/DoDEA Data, Analytics & AI Modernization (HE125426RE037)** →
    `Identified` / WATCH. Single-award FFP IDIQ, Total SB Set-Aside, NAICS 541512,
    PSC DA01; ceiling $47M, guaranteed minimum $25K; base + 4 option years + FAR
    52.217-8. LOE ~396 person-months/yr (33 FTE). Federal rubric SOLO score **4.75/10
    (Moderate)**; **Pwin carried at 5%** (not band-default 25%). Gate 1 PASS on all
    kill triggers, overridden by Step Zero (cancellation) + capacity mismatch
    (396 PM/yr vs. 3-person Montana-committed bench) and no DoD/K-12/Ed-Fi/Fabric
    past performance (F4). CMMC Level 1 (DFARS 252.204-7021) vs. Level 2 (PWS 3.8 /
    CUI-marked TO1) conflict noted UNRESOLVED. Re-check 2026-09-15; monitors
    `HE125426RE037` + `DoWEA-PSN-26-002`.
  - Classified **WATCH, not No-Bid-final** — no formal No-Bid DOCX produced; the
    re-solicitation decision is unmade (Akil written lane call due 2026-08-26).
- **Deliverables (out-of-repo, delivered to owner for review):** WATCH brief
  `Watch_DoWEA_DataAnalyticsAI_HE125426RE037_20260819.docx` and CO-inquiry email
  draft `Email_DoWEA_CO_Inquiry_HE125426RE037_20260819.docx`. Internal Capture &
  Compliance work product — intentionally **not** committed to the repo.
- **Process — recurring capture item added** (`docs/capture_cadence.md`):
  sources-sought notices under NAICS 541512/541519 now explicitly join the weekly
  SAM/DSBS sweep. Loss point on this pursuit was the related sources-sought
  `DoWEA-PSN-26-002` (closed 2026-07-29), not the 2026-08-25 solicitation due date.
- No change to `As_Of_Date` (`Dashboard!C4`); workbook re-validated — formula count
  unchanged (254), zero error cells.

### Removed — Three items cleared from Active Blockers (2026-08-13, owner-directed, 2nd request)
Per repo owner (Khaalis Wooden), the following are **resolved and are not active
blockers**. They were removed from the dashboard `.blockers-list` and must not be
re-added by any future "authoritative set" refresh (now codified as Hard Rule #10
in `CLAUDE.md`):

- WA Secretary of State foreign entity registration (~$180) — gates WA SLED delivery (FSIPAP downstream)
- Montana firearms-entities certification (Grace Waring) — pre-execution item, Montana Master AI award
- eMACS Profile 2 awarded-vendor upgrade — verify completed before Montana contract signature

This corrects the same-day "Active Blockers refreshed" entry below, which had
re-listed these three. The remaining Active Blockers are GSA MAS Refresh 31 and
SOC 2 Type II only.

### Changed — August 2026 mid-month BD update logged (2026-08-13)
Consolidated the 8/13 BD Command Center update (RavenOne channel + CAGAIL/ICAT,
FSIPAP, Montana, NIST QNAP, WA DES 13225) into the system-of-record workbook and
the leadership dashboard. Advanced the snapshot reference date `Dashboard!C4`
(`As_Of_Date`) from **08/05/2026 to 08/13/2026**.

- **Pipeline — 7 new rows (OPP-031 … OPP-037):**
  - **OPP-031 — CMS ICAT RFI (270196, HHS-RADV)** → `Capture`. Teamed with CAGAIL
    LLC (PRIORITY, opportunity-scoped; NDA-before-substance). Solo 5.60 / teamed
    6.38; Pwin 45–50%. KPMG structurally conflicted incumbent. Drafting confined
    to Mon 8/17 to protect FSIPAP; CAGAIL NDA drafted 8/12, execution + scope memo
    due 8/14; RFI due 8/20 10:00 ET. Notes carry the unresolved "Shan" prime /
    Gate-0-COI risk and the two KW go/no-go decisions due 8/14.
  - **OPP-032 — NIST QNAP (RFQ1816699 / NB676020-26-01781)** → `Capture`. Closed
    7/1; TES Consultants prime, VBX technical-sub workshare posture (PhD quantum
    key personnel) on the pending award only.
  - **OPP-033 — WA DES 13225 CAT Tool** → `No-Bid` (8/13). Gate 1 vendor-type
    mismatch (COTS SaaS + live demo; VBX = integrator). Salvaged WA purchaser
    intel into the FSIPAP account map.
  - **OPP-034 — VA Digital GI Bill RFI (36C10D26Q0186)** → `Qualified`
    (PURSUE-CONDITIONAL). RavenOne channel; 4.70 Moderate, 25% Pwin; RFI due
    9/11. Pre-conditions: RavenOne Gate 0 → NDA → teaming w/ workshare floor.
  - **OPP-035 — VA PATS-R (36C10B26Q0662)** → `Identified` (WATCH). RavenOne
    channel; prelim 4.80 (low conf.); SAM alert by 8/14, re-score at strategy
    release.
  - **OPP-036 — CDC KMTSS (SSN26-7571-CDC96901)** → `No-Bid` (niche-sub-only).
    RavenOne channel; 3.75 Low, 10% Pwin.
  - **OPP-037 — VA BioDose 23.x** → `No-Bid` (KILLED at Gate 1). RavenOne
    channel; decline sent with DGB redirect. Authoritative record — do not
    regenerate.
- **Pipeline — OPP-024 WA HCA FSIPAP** advanced `Qualified` → `Capture`
  (StageDate 08/13), notes refreshed for Posture B, governing 8/19 17:00 PT
  deadline, DTR gap, and the WA DES 13225 account-map intel.
- **Screenings — 6 new rows (#68–#73):** RavenOne Enterprises LLC (Charles M.
  Cedeno; HUBZone + SDVOSB self-reported; PENDING-Gate-0), CAGAIL LLC (Lavanya
  Kanchadapu; PRIORITY, opportunity-scoped), Vedic Professional Services,
  WhitworthKee, Allele Consulting (all PENDING pending 8/14 classification), and
  IronHull USA LLC (Robert Foucha; WATCHLIST, firm #8).
- **NDAs — 3 executed NDAs logged (#23–#25):** Vedic Professional Services
  (8/6), WhitworthKee (8/13), Allele Consulting (8/13). The CAGAIL NDA (drafted
  8/12) is **not** in the executed register — execution is due 8/14.
- **Meetings — 2 rows (both 8/13):** CAGAIL ICAT teaming call (structure change,
  "Shan" prime risk, risk memo + approved language block) and the RavenOne
  intro (four VA/CDC opportunities surfaced; decision email drafted).
- **Dashboard — Active Blockers refreshed.** ⚠️ **Superseded** by the "Three
  items cleared" entry above: this refresh incorrectly re-listed the WA
  foreign-entity registration, Montana firearms-entities certification, and
  eMACS Profile 2, which the owner had already declared resolved. The correct
  standing set is **GSA MAS Refresh 31 and SOC 2 Type II only**. (Also removed
  the resolved Advocate IT teaming item and the dormant Maryland eMMA item.)
- **Dashboard (HTML) — default snapshot advanced to 08/13/2026**
  (`STATE.asOfDate` + the as-of input), and **GSA MAS SIN 54151HEAL removed from the footer** to honor the
  standing "SIN suppressed from all document furniture pending Refresh 31"
  rule on this publicly-served artifact (CAGE + UEI remain).
- **Validation:** workbook recomputed clean (254 formulas, cached results
  refreshed via an in-place recalc; LibreOffice was unavailable in the build
  environment). `verify_parse.js` passes all 11 HTML-vs-workbook metric checks
  at As_Of 08/13/2026.
- **Flagged for the owner (not auto-logged):** the Saarthee LLC SSA (7/6) is
  still absent from the `Agreements` register — deferred pending confirmation of
  the instrument type + filename rather than fabricate them.

### Changed — OPP-022 CBO SENTRY closed as No-Bid; DSBS screening batch logged (2026-08-05)
- **Pipeline — OPP-022 (CBO SENTRY IT Support BPA, CB26-RFQ0012) closed as
  `No-Bid`** (StageDate 08/05/2026). Joint TES × VBX decision at the 8/5 monthly
  sync, five days ahead of the 8/10 1300 ET deadline — TES will not prime, VBX
  will not sub. Gate 1 passed; the pursuit fails Gate 2 on economics: Model C
  score 5.35/10 (Moderate, 25% Pwin) inside the 5.0–5.5 window requiring named
  gap closures, none of which were secured (signed TA with workshare floor +
  SMA 2 exclusivity; a past-performance reference slot; VBX named in Factor 3).
  Net EV ≈ $16.4K over five years (~$3.3K/yr) against the $5M ARR target; all
  four scoring gaps structural. The $4M est. value drops out of active-pipeline
  TCV automatically via the existing No-Bid stage exclusion. Full rationale,
  retained work product, and the two Gate 1 lessons (vehicle-economics screen;
  subcontractor citability test) captured in the row's Notes.
- **Screenings — DSBS outreach batch DSBS-2026-08-001 logged (#64–67, screen
  date 08/05/2026)**: Total Technology Solutions (TTS) — PRIORITY; Sampson,
  Jefferson & Associates (SJA) — PRIORITY; Triton Light Medical (TLM) —
  WATCHLIST (opportunity-contingent); BuenaVista Information Systems (BVIS) —
  WATCHLIST (SAM registration expired 1/6/26; 90-day recheck due 11/5/26).
- **Meetings** — logged the 8/5 TES Consultants monthly sync (joint SENTRY
  no-bid; next step: redirect TES to set-aside-accessible RFQs, ≥2 qualified
  pursuits scored by 8/31).
- Advanced the snapshot reference date `Dashboard!C4` (`As_Of_Date`) from
  07/21/2026 to **08/05/2026**.
- Workbook recalculated clean (254 formulas, 0 errors); `verify_parse.js`
  passes all 11 HTML-vs-workbook metric checks.

### Changed — Advocate IT teaming blocker resolved (2026-07-22)
- Removed the "Advocate IT teaming agreement (Thomas Duffy) — not executed"
  item from the dashboard **Active Blockers** list: a three-way teaming
  agreement between Advocate IT, AG Grace, and VBX has been signed. GSA MAS
  Refresh 31 remediation remains the sole standing blocker.

### Added — No-Bid & Screening Log section on the dashboard (2026-07-21)
- New full-width section between the pipeline/scenario row and Active Blockers,
  rendering every `Pipeline` row in the `No-Bid` or `Lost` stage: opportunity,
  decision pill, decision date (Stage Date), and rationale (Notes, clamped to
  three lines with the full text on hover).
- HTML-only (`renderScreeningLog()` in the dashboard); the data was always in
  the workbook — previously no dashboard surface displayed these rows. They
  remain correctly excluded from active-pipeline counts, TCV, and scenario
  math, and the only prior trace was the "New Pipeline Opps" cadence count.
### Added — Three finalized submissions logged to Pipeline (2026-07-21)
- Logged three finalized responses to the `Pipeline` sheet (OPP-028 through
  OPP-030). All three were transmitted 7/21/2026 by 7:00am CT — ahead of every
  deadline — and now sit at `Submitted` stage (StageDate 07/21/2026):
  - **OPP-028 — MARFORRES AI Manpower & Readiness (Sources Sought
    M6786126IMKMAI)**: USMC Forces Reserve (MFR G-1 / MCIRSA). AI-enabled
    manpower modeling, readiness analytics, and personnel allocation
    (IRR/SMCR). Response and cover letter finalized via the
    solicitation-response gates; send scheduled by 7/29 (due 7/30 12:00pm CDT),
    gated on the metric/certification checklist. NAICS not stated on the
    notice; set-aside blank, with SB shaping questions embedded in the
    transmittal.
  - **OPP-029 — DHA ARMOR Integrated Workforce & Readiness Platform (RFI
    ARMOR001)**: Defense Health Agency (DHMS-CD). Tier 1 fit; all five use
    cases addressed within the 10-page cap; §3.5 OCI access granted. Send
    target 7/22 12:00pm EDT (hard wall worst-cased at 5:00pm). The GSA SIN
    line ruling was resolved 7/21 (owner): the conservative "none currently
    held" wording stands — reconciled state per the CC Blockers panel is SIN
    54151HEAL held but under Refresh 31 remediation (7 deficiencies open); the
    cite-SIN alternative was declined. Anticipated RFP flagged as a pipeline
    priority for scoring.
  - **OPP-030 — USGS NEIC AI/ML & Data Streaming Development (Sources Sought
    140G0226Q0049)**: USGS / DOI (OAG-Denver). Tier 2/adjacent fit with candor
    positioning (transferable production AI/data engineering, no seismology
    claims); five software-development task areas addressed. Send target 7/23
    EOD (due 7/24, deadline-timezone discrepancy worst-cased to EDT). Open
    pre-send check: verify the SAM Attachments/Links tab for response
    instructions.
- No value booked on any of the three (Sources Sought / RFI stage — no
  published ceilings), so active-pipeline TCV and win-rate scenario math are
  unaffected.
- Advanced the snapshot reference date `Dashboard!C4` (`As_Of_Date`) from
  07/19/2026 to **07/21/2026** so the new entries count in the trailing
  windows (New Pipeline Opps T-30d: 6 → 9).
- Workbook recalculated clean (254 formulas, 0 errors); `verify_parse.js`
  passes all 11 HTML-vs-workbook metric checks.

### Added — Five July pursuits logged to Pipeline (2026-07-19)
- Consolidated the July qualification batch into the `Pipeline` sheet (OPP-024
  through OPP-027; the fifth pursuit, IHS WebEHRS, was already logged as OPP-023
  and its RFI response confirmed transmitted before deadline):
  - **OPP-024 — WA HCA FSIPAP (RFI 2026HCA13)**: `Qualified`. The only live
    respond in the batch — narrow policy-transformation lane only, RFI due
    8/19/26 5pm PT, ≤10 pages, B&P ≤$6K. Score 4.6/10 Moderate. No value booked
    (no published ceiling), so it cannot distort active-pipeline TCV or the
    win-rate scenario math.
  - **OPP-025 — WA DRS E-File Tax Reporting (RFP 26-03)**: `No-Bid` (Gate 1,
    7/10 — MQ 1.3 restricts offerors to IRS-authorized e-file providers).
  - **OPP-026 — Army Enterprise IT Support, OTSG/MEDCOM (W9124J-27-R-ENTR)**:
    `No-Bid` prime and sub (7/10 — Secret FCL, CMMI-SVC L3, vendor-type
    mismatch; SSN window closed 7/16).
  - **OPP-027 — DoS BASE (19AQMM26N0296)**: `No-Bid` as prime (7/7 — geospatial
    domain mismatch); conditional sub lane expired ~7/15 with no geospatial
    prime surfaced, collapsing to a straight no-bid.
- Advanced the snapshot reference date `Dashboard!C4` (`As_Of_Date`) from
  06/08/2026 to **07/19/2026**.
- Workbook recalculated clean (254 formulas, 0 errors); `verify_parse.js`
  passes all 11 HTML-vs-workbook metric checks against the new as-of date.

### Changed — Insurance premiums added to Yearly Expense Budget (2026-07-09)
- Four annual business-insurance policies were folded into the operating expense
  base on `Targets` (cell C6): Errors & Omissions ($3,035), Cyber Liability
  ($8,500), General Liability ($353), and Workers' Compensation ($473) — total
  **$12,361** in annual premiums (premiums only; policy taxes/fees excluded).
- **Yearly Expense Budget** rises from **$212,270** to **$224,631**.
- P/L reconciliation recomputes off C6 via formula (C12/C13):
  - **Run-Rate P/L** (Confirmed Revenue $164,400 − Budget) moves from –$47,870 to
    **–$60,231**.
  - **Gap to Break-Even** moves from $47,870 to **$60,231**.
  - **Gap to ARR Target** is unchanged at **$335,600** (a function of the ARR
    target and confirmed revenue, not the expense budget).
- HTML dashboard income-statement `DEFAULTS` (`expenseBudget`, `runRatePL`,
  `breakEvenGap`) updated to mirror the workbook; the P/L drill-down subtitle now
  renders the Run-Rate P/L figure dynamically instead of a hardcoded string.

### Fixed — HCPSS revenue start date corrected to May 2026 (2026-07-09)
- The HCPSS project did not begin until May 2026, so the four pre-start monthly
  retainer invoices were removed from `Revenue_Ledger`:
  - `INV-2026-001` (1/31/2026), `INV-2026-003` (2/28/2026),
    `INV-2026-005` (3/31/2026), `INV-2026-007` (4/30/2026) — $11,200 each.
- HCPSS now bills from `INV-2026-009` (5/31/2026) forward. The First Brands
  Group retainer stream (Jan → Jun) is unchanged. Ledger is now 8 invoices
  (was 12).
- Downstream figures recalculate off the ledger via formula (no hardcoded
  edits): **Revenue Booked YTD** at As-Of 6/8/2026 drops from $68,500 to
  **$23,700** (−$44,800); trailing-window revenue (T-7d/T-30d/T-91d) and the
  Net P/L "actuals" row follow suit.
- The annualized run-rate inputs on `Targets` (C9 HCPSS = $134,400, C10 FBG =
  $30,000) are intentionally **unchanged**: run-rate P/L and the break-even /
  ARR gaps are forward steady-state figures at the current $11,200/mo billing
  rate, which the start-month correction does not alter.
- Recalc validated: 0 formula errors across 254 formulas.

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
  added screenings rows 57–61 (BAC, NCP, et al.) and one new partner meeting,
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
