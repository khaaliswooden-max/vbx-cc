# Capture Process — Recurring Cadence

Standing, recurring capture-process items for the VBX BD Command Center. This file
records **process**, not opportunity data. Opportunity records live in the workbook
`Pipeline` sheet; scoring authority is the `visionblox-capture` skill
(`references/scoring-engine.md`).

---

## Weekly SAM.gov / DSBS sweep

**Owner:** Khaalis Wooden · **Cadence:** weekly

Scan for new and amended opportunities across the VBX NAICS set and log qualifying
notices into the `Pipeline` sheet at stage `Identified`.

### Notice types in scope
- **Solicitations / RFQs / RFPs** — the active buy.
- **Sources Sought / RFIs** — the shaping window. **These are in scope and are
  first-class sweep targets, not optional.**

### NAICS watched
541511 · 541512 · **541519** · 518210 · 541611 · 541330

> **Added 2026-08-19 (recurring item):** Sources-sought notices under **NAICS 541512
> and 541519** explicitly join the weekly sweep. Rationale — on the DoWEA/DoDEA Data,
> Analytics & AI Modernization pursuit (`HE125426RE037`), the real loss point was the
> related sources-sought **`DoWEA-PSN-26-002`, which closed 2026-07-29 with no VBX
> response** — not the 2026-08-25 solicitation due date. Missing the sources-sought
> stage forfeits the shaping window and, on single-award IDIQs, the pursuit itself.
> The sweep must catch the SS, not just the RFP.

### Weekly output
1. New qualifying notices → `Pipeline` rows (`Identified`), with SAM monitor keys in Notes.
2. Amendments to tracked opportunities → update the corresponding row's Stage Date + Notes.
3. Cancellations → set `WATCH` (do **not** produce a formal No-Bid until the
   re-solicitation decision is made) or `No-Bid` per the scoring gate.
4. Re-check dates set for every `WATCH` row.

---

## Related monitors (active)

| Monitor key | Why watched | Re-check |
|---|---|---|
| `HE125426RE037` | DoWEA/DoDEA Data, Analytics & AI IDIQ — CANCELLED 2026-08-17; re-issue likely | 2026-09-15 |
| `DoWEA-PSN-26-002` | Sources-sought lineage for the above (true engagement point) | 2026-09-15 |
