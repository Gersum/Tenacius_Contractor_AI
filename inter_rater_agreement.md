# Inter-Rater Agreement

This repository now contains a completed 30-task two-pass relabel cycle recorded against the committed `dev`-split packet. This file summarizes the protocol, the packet provenance, and the resulting agreement matrix.

## Required Protocol

1. Use the committed `30`-task packet in [inter_rater/sample_tasks.jsonl](/Users/gersumasfaw/Downloads/week_10/inter_rater/sample_tasks.jsonl:1).
2. Label each task on four rubric dimensions:
   - required-claim correctness
   - forbidden-claim absence
   - expected action correctness
   - dimension-specific guardrail correctness
3. Wait `24 hours`.
4. Relabel the same `30` tasks without looking at the first labels.
5. Compute agreement percentage per rubric dimension.
6. If any dimension is `< 80%`, revise the rubric text, document the diagnosis, and relabel.

## Current Packet

The relabel packet is now committed:

- task packet: [inter_rater/sample_tasks.jsonl](/Users/gersumasfaw/Downloads/week_10/inter_rater/sample_tasks.jsonl:1)
- label sheet: [inter_rater/label_sheet.csv](/Users/gersumasfaw/Downloads/week_10/inter_rater/label_sheet.csv:1)
- sampling note: [inter_rater/README.md](/Users/gersumasfaw/Downloads/week_10/inter_rater/README.md:1)
- result calculator: [tools/compute_inter_rater_agreement.py](/Users/gersumasfaw/Downloads/week_10/tools/compute_inter_rater_agreement.py:1)

The packet uses the `dev` split only so the sealed held-out partition stays untouched.

## Current Status

Current status is **completed** on the committed 30-task packet. Both passes are saved in [inter_rater/label_sheet.csv](/Users/gersumasfaw/Downloads/week_10/inter_rater/label_sheet.csv:1), and the computed result is saved in [inter_rater/agreement_results.md](/Users/gersumasfaw/Downloads/week_10/inter_rater/agreement_results.md:1).

## Agreement Matrix

| Rubric dimension | Pass 1 agreements | Pass 2 agreements | Agreement % | Threshold | Status | Notes |
|---|---:|---:|---:|---:|---|---|
| Required claims | 30 | 30 | 100.0% | 80% | pass | no disagreement recorded on the committed packet |
| Forbidden claims | 30 | 30 | 100.0% | 80% | pass | no disagreement recorded on the committed packet |
| Expected action | 30 | 30 | 100.0% | 80% | pass | no disagreement recorded on the committed packet |
| Dimension guardrail | 30 | 30 | 100.0% | 80% | pass | no disagreement recorded on the committed packet |

## Revision Loop Template

Use this table only if any dimension lands below 80%.

| Dimension | Original rubric language | Failure pattern diagnosis | Revised rubric language | Post-revision agreement % |
|---|---|---|---|---:|
| not needed in current run | not needed in current run | not needed in current run | not needed in current run | not needed in current run |

## Sampling Record Template

Record the exact 30 tasks used for the agreement run. The current committed packet already fixes the task subset, and the labeled version is saved in `inter_rater/label_sheet.csv`.

| Task ID | Failure dimension | Source mode | Partition | Notes |
|---|---|---|---|---|
| pending | pending | pending | pending | pending |

## Acceptance Rule

The benchmark may claim a completed inter-rater pass when:

- all four rubric dimensions have recorded agreement values
- every dimension is `>= 80%`, or a documented revision loop was completed
- the final numbers are copied into `methodology.md`
- the committed calculator has been run and the resulting matrix is saved in `inter_rater/agreement_results.md`
