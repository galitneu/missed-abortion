# Missed Abortion Coding Study

Multi-agent LLM pipeline for classifying "missed abortion" (הפלה נדחית) clinical episodes
from raw Hebrew hospital admission-note text, for a doctoral thesis research project.

**Contains real (partially redacted) patient clinical data. Private repository — do not make public
or share outside the study's approved access list.**

## How it works

1. **Linkage** (deterministic, not an LLM): raw admission rows are grouped into "episodes"
   (all records belonging to one woman's missed-abortion event), by admission number and by
   row-level text-similarity cross-linking across admissions. See `scripts/extract_all_episodes.py`.
2. **Coding**: each episode is coded independently by 3 LLM coder agents against the protocol
   in `codebook/code_episodes.workflow.js` (the `CODEBOOK` and `SCHEMA` constants there are the
   canonical, most up-to-date coding instructions — 33 fields per episode).
3. **Merge**: a deterministic majority-vote step (`majorityMerge` in the same file) produces one
   consensus answer per field, and flags every field where the 3 coders did not fully agree
   (`disagreements`).

## Layout

- `codebook/code_episodes.workflow.js` — the full pipeline script (Workflow-tool format): codebook
  text, output schema, prompt builder, and the merge logic. This is the source of truth for coding
  rules; other scripts assume its schema.
- `scripts/` — extraction/selection/build utilities (Python). `extract_all_episodes.py` builds the
  full episode cache from the raw admissions export; `select_batch.py` / `select_random_batch*.py`
  slice batches out of that cache for coding; `recompute_merge_80.py` re-runs the merge logic over
  already-coded raw coder output (no re-coding) after a merge-logic fix; `build_output_xlsx.py`
  produces the reviewer-facing Excel workbook; `build_database.py` builds/rebuilds `db/missed_abortion.sqlite`.
- `data/coding_results/*.json` — one entry per episode: `episode_id`, `admission_nos`, all 3 raw
  coder outputs, `consensus`, `disagreements`, `n_disagreements`.
- `data/raw_text/*/` — the raw chronological source text per episode (input to coding).
- `data/episodes_meta/*.json` — episode selection metadata for the random batches.
- `output/*.xlsx` — reviewer-facing 3-sheet workbooks (overview / detail / full text), color-coded
  for disagreements and record-mixup suspicion.
- `reports/*.md` — Hebrew disagreement-analysis reports from review agents, with root-cause
  breakdowns and codebook-fix recommendations.
- `db/missed_abortion.sqlite` — all episodes + coder outputs + consensus in one queryable file,
  plus an empty `physician_review` table for structured reviewer feedback (see schema in
  `scripts/build_database.py`). Rebuild anytime with `python3 scripts/build_database.py`.

## Batches coded so far

- `chronological_40` (V2EP001-040): first 40 episodes chronologically from 1 Dec 2023.
- `random_80` (RNDEP001-040 + RND2EP001-040): two batches of 40 randomly sampled episodes
  (non-overlapping with each other or with the chronological batch), coded after codebook fixes
  from the chronological-batch review, used to validate the fixes on unseen data.
- Full episode pool is ~974 episodes (admissions from 1 Dec 2023 onward) — most are not yet coded.

## Known open items (see `reports/random_80_disagreements.md` for full detail)

- D_C_treatment is the most disagreement-prone field (OR-intake-without-explicit-post-op-note
  ambiguity) — needs a codebook default-presumption rule.
- G (gravidity) computed-from-subcomponents inconsistency when not stated as a single number.
- 10 prioritized codebook-fix recommendations pending a decision on which to adopt.
