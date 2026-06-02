# Security Policy

This repository contains confidential and proprietary business development information for Visionblox LLC. Treat every file as sensitive unless explicitly documented otherwise.

---

## 1. What is sensitive in this repo

The following data classes are considered **Confidential** and may also be subject to **third-party NDAs**:

- Partner names and contact details (any row in `Screenings`, `NDAs`, `Agreements`, `Meetings`)
- Pipeline opportunity details (any row in `Pipeline`, including names, agencies, values, NAICS codes)
- Revenue figures (any row in `Revenue_Ledger`, including client names and invoice amounts)
- Expense detail (any row in `Expense_Ledger`)
- Active project execution data (`Active_Projects`)
- Internal targets and projections (`Targets` sheet values)
- Internal feedback (`Feedback` sheet)
- References to the CAHSP and GRHD frameworks (proprietary IP under Zuup Innovation Lab)

The following are considered **Internal but not NDA-restricted**:
- Source code (`scripts/`, `dashboard/`)
- Documentation (`README.md`, `CLAUDE.md`, `CHANGELOG.md`, `SECURITY.md`)
- Brand standards (colors, fonts, layout patterns)
- Workbook structure (sheet names, column conventions)

---

## 2. What never gets committed

**Hard rules** — violation is a security incident:

1. **No populated workbooks in any committed file.** Generated `*.xlsx` files belong in `output/` (gitignored). The only XLSX file that may be committed is `data/targets_template.xlsx`, which contains schema only and zero real values.

2. **No partner data in source files.** Seed/back-fill blocks in `scripts/build_command_center.py` must not contain real partner names, real meeting outcomes, or real pipeline opportunity names when committed. Use the gitignored `scripts/_seed_data_local.py` pattern for any real-data back-fills.

3. **No screenshots of populated dashboards** in `README.md` or anywhere else in the repo. If a screenshot is needed for documentation, generate it from the schema-only template.

4. **No revenue or P/L figures in any committed text** — even illustratively.

5. **No executed NDA documents** anywhere in the repo. These are governed by their own retention policy.

6. **No `.env` files**, API keys, credentials, or service account JSON.

---

## 3. Pre-commit checklist

Before every commit, run through this:

- [ ] `git diff` reviewed — no real partner names, no real dollar figures, no real opp names
- [ ] No files in `output/` are being committed
- [ ] No screenshots include real data
- [ ] `data/` directory contains only schema/template files
- [ ] If `scripts/build_command_center.py` was modified, any back-fill blocks were reverted or moved to `_seed_data_local.py`
- [ ] If CHANGELOG.md was updated, no specific opportunity names or partner names were included

---

## 4. Repository access

This repository is **private**. Access is limited to:

- The Director of Enterprise Capture & Compliance (Khaalis Wooden)
- Authorized Visionblox personnel acting within scope of their engagement
- Such Claude Code / agentic AI tools as the repo owner has explicitly authorized

Do not add collaborators, transfer ownership, change visibility to public, or create forks without written authorization from the repo owner.

---

## 5. Reporting a security concern

If you discover that confidential data has been committed, exposed in logs, or leaked to a public surface:

1. **Do not** open a public issue
2. **Do not** publish a fix that mentions the leak in the commit message
3. **Email** the repo owner immediately:

   **Khaalis Wooden, MBA**
   khaalis.wooden@visionblox.com
   (256) 988-1130

4. **If credentials may have been exposed**, also notify the CISO:

   **Tony Paul**
   Visionblox LLC — CISO

5. **For NDA-implicated exposures** (a partner's confidential information has been leaked), follow Visionblox standard NDA breach notification procedure as set by the Director of Enterprise Capture & Compliance.

---

## 6. Data destruction

When a workbook or dashboard artifact is no longer needed:

- Delete from `output/` (which is local-only)
- Empty the OS trash / recycle bin
- For artifacts that were emailed or shared externally, follow Visionblox standard document retention and destruction policy

Do not rely on `git rm` alone to remove sensitive data — once committed, files persist in git history and require `git filter-repo` or similar to truly remove. If you commit sensitive data by accident, contact the repo owner immediately to coordinate a history rewrite.

---

## 7. AI training opt-out

All content in this repository is **opt-out of any AI model training workflow**. This includes:

- No use in fine-tuning datasets
- No inclusion in RAG corpora visible outside Visionblox
- No upload to third-party AI tools whose terms permit training on submitted content

Claude Code sessions in this repository operate under Anthropic's Zero Data Retention configuration when available. If you're unsure whether a tool retains and trains on submitted content, default to not using it on this repo.

---

## 8. Vulnerability disclosure for the code itself

If you discover a security vulnerability in the workbook builder or HTML dashboard (e.g., XSS in the HTML, code injection in the Python builder), report it directly to the repo owner using the contact information in §5. We will acknowledge within 5 business days.

There is no bug bounty program. This is internal tooling.

---

Copyright (c) 2026 Visionblox LLC. All Rights Reserved.
