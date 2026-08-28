# How to add or edit a Pipeline opportunity (the text feed)

The `Pipeline` sheet's source of record is **`data/pipeline_feed.jsonl`**, not the
binary workbook. Editing the feed instead of the `.xlsx` is what lets two people
(or two Claude sessions) add pipeline rows at the same time without a merge
conflict, and it stops OPP-IDs from colliding.

## Why

`VBX_Command_Center_v1.1.xlsx` is a binary file. Git cannot merge binaries, so if
branch A and branch B both add a `Pipeline` row, they conflict on the **entire
workbook** and someone has to re-resolve by hand — and because both branches grab
the same "next" OPP-ID, the IDs collide too. The feed is plain text with **one JSON
object per opportunity on its own line**, so git merges concurrent additions
automatically, and OPP-IDs are handed out deterministically when the feed is synced
on `main`.

## Add a new opportunity

1. Append **one line** to `data/pipeline_feed.jsonl`:

   ```json
   {"key": "region4-26-14", "name": "Region 4 ESC RFP 26-14 — AI & Total Cloud Solutions", "client": "Region 4 ESC (OMNIA lead agency)", "naics": "541511", "stage": "No-Bid", "value": null, "date_identified": "2026-08-19", "stage_date": "2026-08-19", "owner": "Khaalis Wooden", "notes": "..."}
   ```

   - **`key`** — required, unique. A stable handle you choose (the solicitation
     number or a slug). It identifies the record regardless of its OPP-ID.
   - **Do NOT set `opp_id`.** The sync assigns the next free `OPP-0NN` and freezes
     it (writes it back into your line). This is what prevents ID collisions.
   - `stage` ∈ `Identified | Qualified | Capture | Submitted | Awarded | Lost | No-Bid`.
   - `value` — integer dollars or `null`. `date_identified` / `stage_date` — ISO
     `YYYY-MM-DD`. `notes` — free text (keep it on the one line; JSON escapes any
     quotes/newlines for you).

2. Preview locally (writes nothing):

   ```bash
   python scripts/sync_pipeline_from_feed.py --check   # validate + preview id
   ```

   `--check` validates the feed and shows which OPP-ID your row *would* get, without
   touching any file. **Do not** run the plain (non-`--check`) sync just to freeze an
   ID on your branch: if two branches each froze the same next id, the git merge
   keeps both as a duplicate and the main sync fails. IDs are frozen at exactly one
   place — the CI sync on `main` — so leave `opp_id` unset and let it assign.

3. Commit the **feed** (and any DOCX record). You do **not** need to commit the
   regenerated workbook from your branch — CI regenerates and commits it on `main`
   after merge, where there's no concurrency. On a PR, CI runs `--check` to
   validate your feed line.

## BD posture and technical detail

The same feed line also carries the structured BD-posture and technical-scope
fields that the operations and delivery teams asked for. They used to be buried
inside the free-text `notes` blob, which the dashboard never rendered. All of them
are **optional** — a record with none of them still syncs — but a pursuit that
anyone has to plan support for should carry them.

They are written to a second sheet, **`Opportunity_Detail`**, one row per Pipeline
row in the same order, joined on Opp ID. They are *not* extra `Pipeline` columns:
that sheet keeps its 10-column contract with the workbook and the HTML parser
(CLAUDE.md Hard Rule #3).

| Field | What goes in it |
|---|---|
| `bd_posture` | `Prime` · `Sub` · `Prime or Sub` · `Undecided` · `Not pursuing` |
| `teaming_status` | `Solo` · `Partner needed` · `Partner identified` · `In discussion` · `NDA executed` · `Teaming agreement executed` · `Teaming declined` · `N/A` |
| `response_due` | ISO `YYYY-MM-DD` — when the response is **due**. Not the same as `stage_date`, which is when the row last moved. |
| `next_milestone` | The next concrete action |
| `milestone_owner` | Who owns it |
| `win_theme` | Why we win — the discriminator, not the score |
| `scope_summary` | Plain language: what VBX would actually build or run |
| `capabilities_required` | JSON array — technical capabilities the work needs |
| `labor_categories` | JSON array — the LCATs or roles the solicitation names |
| `compliance_gates` | JSON array — CMMC, FedRAMP, SOC 2, HIPAA, ATO, clearances… |
| `place_of_performance` | Onsite / remote / hybrid, and where |
| `period_of_performance` | Base + options |
| `staffing_gap` | Where the bench is short today |

The three array fields also accept a plain `"; "`-joined string if that is easier
to hand-edit; both forms round-trip identically. Example:

```json
{"key": "…", "…": "…", "bd_posture": "Prime", "teaming_status": "Solo", "response_due": "2026-09-08", "next_milestone": "Re-score at RFP release", "milestone_owner": "Khaalis Wooden", "win_theme": "…", "scope_summary": "…", "capabilities_required": ["FHIR — Da Vinci CRD + PAS", "Data engineering"], "labor_categories": ["Principal Architect"], "compliance_gates": ["SOC 2", "ATO"], "place_of_performance": "Remote", "period_of_performance": "Base + 4 options", "staffing_gap": "…"}
```

`--check` reports how many records carry detail. Leaving a field out is fine and
honest — the dashboard prints "Not yet recorded" rather than hiding the gap, so a
blank is visible to whoever should fill it. **Prefer a blank to a guess.**

### Where it shows up

In the dashboard, click any pipeline row — on the main Active Pipeline table or
inside the pipeline drill-down — to open that opportunity's brief: a facts strip
(stage, posture, value, NAICS, owner, identified, response due) over two columns,
**BD Posture** and **Technical Scope**, with the original capture notes underneath.
The drill-down table also gains Posture and Response Due columns.

### What is published, and what is not

GitHub Pages is public and search-indexable, so `scripts/build_leadership_feed.py`
applies a disclosure allowlist to the copy the Pages workflow serves. The
committed workbook is never modified.

| Published | Withheld |
|---|---|
| **Every `Opportunity_Detail` field** — `bd_posture`, `teaming_status`, `response_due`, `next_milestone`, `milestone_owner`, `win_theme`, `scope_summary`, `capabilities_required`, `labor_categories`, `compliance_gates`, `place_of_performance`, `period_of_performance`, `staffing_gap` | the whole `Pipeline` **Notes** column |

**Everything you type into these fields is public.** The BD half was withheld
when the sheet was first published, on the reasoning that it states VBX's own
position rather than the solicitation's requirement; the owner reversed that on
2026-08-28 so leadership reads the same brief on the public link that they read
internally. There is no longer a "safe" column — the old rule of putting our
standing in `staffing_gap` no longer protects it.

So when you fill these in:

- Write every cell as if a competitor will read it, because one can.
- `staffing_gap` is now a **public** list of what VBX does not hold. Still record
  it honestly — the gap has to stay visible to the people planning the pursuit —
  but keep it to the capability, not the story behind it.
- **No named individuals and no third-party company names**, in any field.
- Anything candid — partner names, Pwin scores, EV math, POC contacts, no-bid
  rationale — goes in the record's `notes`, which becomes `Pipeline!J` and is the
  one column still withheld.

On the public dashboard the Capture Notes panel is absent; every other panel now
shows the same content it shows internally. The build writes no output and fails
the deploy if anything outside the allowlist survives.

## Edit an existing opportunity

Find its line by `key` (or `opp_id`) and edit the fields in place. Keep `opp_id`
as-is. Run the sync to preview, then commit the feed.

## Rebuild the feed from the workbook (rescue)

If the feed and workbook ever drift:

```bash
python scripts/export_pipeline_to_feed.py          # workbook -> feed (one-way)
```

## Rules

- Never hand-edit the `Pipeline` sheet in the binary workbook to add/edit rows —
  use the feed so merges stay clean.
- The feed is real operational data: it is committed under the owner-authorized
  Rule #1 exception (2026-08-19) but is **never published** (the Pages workflow
  serves only the dashboard + `leadership_feed.xlsx`).
- This flow is for the `Pipeline` sheet only. Other input sheets follow CLAUDE.md
  Workflows C/E.
