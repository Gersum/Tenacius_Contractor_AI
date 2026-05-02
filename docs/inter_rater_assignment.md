# Inter-Rater Relabel Assignment — 30-task cycle

Purpose
-------
Complete a blind inter-rater relabel cycle for the committed 30-task dev-split packet to validate rubric dimensions and compute inter-rater agreement (IRA). The acceptance rule is 80% agreement or better on each major rubric dimension.

Files and links
---------------
- Tasks to relabel: `inter_rater/sample_tasks.jsonl`
- Label sheet: `inter_rater/label_sheet.csv`
- Sampling note: `inter_rater/README.md`
- Agreement calculator: `tools/compute_inter_rater_agreement.py`
- Evidence traces: `eval/trace_log.jsonl`
- Scoring code: `eval/tenacious_bench`

Roles
-----
- Raters: at least 3 human raters (blind to each other's labels)
- Coordinator: collects CSVs, merges, computes IRA, and runs reconciliation

Procedure
---------
1. Coordinator uses the committed `inter_rater/sample_tasks.jsonl` packet and `inter_rater/label_sheet.csv` sheet.
2. Raters receive the labeling sheet with instructions and the blind labeling deadline (suggest 48–72 hours).
3. Raters label independently. Do not discuss during the blind phase.
4. After all labels are in, the coordinator runs `python3 tools/compute_inter_rater_agreement.py` to compute per-dimension percent agreement and flags any items below threshold for adjudication.
5. Wait 24 hours, then run a blind relabel on flagged items or run a consensus reconciliation meeting.

Labeling rubric (columns)
-------------------------
- `task_id`: unique task identifier
- `rater_id`: rater short id (e.g., rater01)
- `public_signal_ok`: 1/0 — did the output respect public-signal restraint?
- `tone_ok`: 1/0 — was Tenacious tone preserved?
- `competitor_gap_ok`: 1/0 — competitor-gap claim accurate / supported?
- `scheduling_ok`: 1/0 — booking/scheduling handoff correct?
- `overall_pass`: 1/0 — acceptable for pipeline handoff
- `comments`: optional free-text justification

Decision rule
-------------
- Per-dimension acceptance threshold: 80% agreement across raters.
- If a dimension fails the threshold, mark for adjudication and either (a) blind relabel by same raters after 24h, or (b) a small reconciliation meeting to resolve disagreements and update the rubric.

Deliverables
------------
- `inter_rater/label_sheet.csv` with both passes filled in.
- `inter_rater/agreement_results.md` and `inter_rater/agreement_results.json` from the calculator.
- A short `docs/inter_rater_report.md` summarizing IRA metrics, failing items, and recommended rubric updates if any dimension is below threshold.

Coordinator checklist
--------------------
- [ ] Use the committed packet and create a working copy of `inter_rater/label_sheet.csv`
- [ ] Send instructions and deadline to raters
- [ ] Collect completed CSVs
- [ ] Merge and compute IRA (script recommended)
- [ ] Flag low-agreement items and run adjudication
- [ ] Generate `docs/inter_rater_report.md` and update `methodology.md` if needed

Quick commands (local)
----------------------
Recompute the inter-rater matrix after both passes are filled:

```bash
python3 tools/compute_inter_rater_agreement.py
```

Notes
-----
- Keep held-out sealed; the committed packet already uses `dev`.
- Use the `eval/tenacious_bench` runner to recompute scores after relabel-driven rubric updates.
