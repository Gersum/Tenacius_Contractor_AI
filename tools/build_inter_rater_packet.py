from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEV_TASKS = ROOT / "tenacious_bench_v0_1" / "dev" / "tasks.jsonl"
OUT_DIR = ROOT / "inter_rater"
PACKET_JSONL = OUT_DIR / "sample_tasks.jsonl"
SAMPLE_CSV = OUT_DIR / "label_sheet.csv"
README_MD = OUT_DIR / "README.md"

DIMENSION_PRIORITY = [
    "tone_style_drift",
    "hiring_signal_overclaiming",
    "bench_overcommitment",
    "competitor_gap_overclaiming",
    "public_signal_reliability",
    "scheduling_handoff_correctness",
    "icp_misclassification",
]

EXTRA_DIMENSIONS = {"tone_style_drift", "scheduling_handoff_correctness"}


def load_tasks() -> list[dict]:
    return [json.loads(line) for line in DEV_TASKS.read_text(encoding="utf-8").splitlines() if line.strip()]


def select_sample(tasks: list[dict]) -> list[dict]:
    by_dimension: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for task in tasks:
        by_dimension[task["failure_dimension"]][task["source_mode"]].append(task)

    for modes in by_dimension.values():
        for task_list in modes.values():
            task_list.sort(key=lambda row: row["task_id"])

    sample: list[dict] = []
    for dimension in DIMENSION_PRIORITY:
        sample.extend(by_dimension[dimension]["programmatic"][:3])
        sample.extend(by_dimension[dimension]["multi_llm_synthesis"][:1])
        if dimension in EXTRA_DIMENSIONS:
            sample.extend(by_dimension[dimension]["multi_llm_synthesis"][1:2])

    sample.sort(key=lambda row: row["task_id"])
    if len(sample) != 30:
        raise ValueError(f"Expected 30 sampled tasks, found {len(sample)}")
    return sample


def write_packet(sample: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with PACKET_JSONL.open("w", encoding="utf-8") as fh:
        for row in sample:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    fieldnames = [
        "task_id",
        "failure_dimension",
        "source_mode",
        "partition",
        "required_claims_pass1",
        "forbidden_claims_pass1",
        "expected_action_pass1",
        "dimension_guardrail_pass1",
        "required_claims_pass2",
        "forbidden_claims_pass2",
        "expected_action_pass2",
        "dimension_guardrail_pass2",
        "notes",
    ]
    with SAMPLE_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in sample:
            writer.writerow(
                {
                    "task_id": row["task_id"],
                    "failure_dimension": row["failure_dimension"],
                    "source_mode": row["source_mode"],
                    "partition": "dev",
                }
            )

    counts_by_dim: dict[str, int] = defaultdict(int)
    counts_by_mode: dict[str, int] = defaultdict(int)
    for row in sample:
        counts_by_dim[row["failure_dimension"]] += 1
        counts_by_mode[row["source_mode"]] += 1

    lines = [
        "# Inter-Rater Packet",
        "",
        "This directory contains the committed 30-task subset for the required two-pass inter-rater agreement run.",
        "",
        "## Contents",
        "",
        f"- [sample_tasks.jsonl]({PACKET_JSONL.name}): exact dev-split task packet to label",
        f"- [label_sheet.csv]({SAMPLE_CSV.name}): fillable pass-1 / pass-2 labeling sheet",
        "",
        "## Sampling policy",
        "",
        "- Partition: `dev` only, to preserve the sealed held-out split",
        "- Per dimension: all `3` programmatic tasks plus `1` multi-LLM synthesis task",
        "- Extra synthesis tasks added for `tone_style_drift` and `scheduling_handoff_correctness` to reach `30` rows total",
        "",
        "## Composition",
        "",
    ]
    for dimension in DIMENSION_PRIORITY:
        lines.append(f"- `{dimension}`: {counts_by_dim[dimension]} tasks")
    lines.extend(
        [
            "",
            f"- `programmatic`: {counts_by_mode['programmatic']} tasks",
            f"- `multi_llm_synthesis`: {counts_by_mode['multi_llm_synthesis']} tasks",
            "",
            "## Labeling rule",
            "",
            "Fill pass 1 first, wait 24 hours, then fill pass 2 without looking back at pass 1.",
        ]
    )
    README_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    sample = select_sample(load_tasks())
    write_packet(sample)
    print(f"Wrote {len(sample)} sampled tasks to {PACKET_JSONL}")


if __name__ == "__main__":
    main()
