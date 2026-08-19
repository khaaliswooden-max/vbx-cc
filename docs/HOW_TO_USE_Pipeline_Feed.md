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
