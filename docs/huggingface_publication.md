# Hugging Face Publication

This repo does not have a Hugging Face MCP or connector in the current Codex session, so publication is handled through a local script plus `huggingface_hub`.

## Prerequisites

- `HF_TOKEN` set in `.env` or shell
- `HF_DATASET_REPO_ID` set to `username/repo_name`
- optional: `HF_MODEL_REPO_ID` reserved for future adapter publication

## Install

```bash
python3 -m pip install -r requirements.txt
```

## Publish the dataset

```bash
python3 training/publish_huggingface_dataset.py
```

Optional explicit repo id:

```bash
python3 training/publish_huggingface_dataset.py --repo-id your-handle/tenacious_bench_v0_1
```

Optional private first pass:

```bash
python3 training/publish_huggingface_dataset.py --private
```

## What gets uploaded

- `tenacious_bench_v0_1/`
- `datasheet.md`
- `methodology.md`
- `audit_memo.md`
- `evidence_graph.json`
- `README.md` snapshot as `repo_readme_snapshot.md`

## Manual follow-up

After publication, copy the final dataset URL into the `Public Artifacts` section of [README.md](/Users/gersumasfaw/Downloads/week_10/README.md:1).
