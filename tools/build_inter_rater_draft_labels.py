from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.tenacious_bench.scoring_evaluator import score_task

SAMPLE_TASKS = ROOT / "inter_rater" / "sample_tasks.jsonl"
OUT_CSV = ROOT / "inter_rater" / "draft_label_suggestions.csv"


def load_tasks() -> list[dict]:
    return [json.loads(line) for line in SAMPLE_TASKS.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_reasoning(task: dict, result_checks: dict[str, bool], notes: list[str]) -> str:
    gt = task["ground_truth"]
    summary_bits = [
        f"expected_action={gt['expected_action']}",
        f"required_claims={'; '.join(gt['required_claims'])}",
        f"forbidden_claims={'; '.join(gt['forbidden_claims'])}",
    ]
    failed = [name for name, passed in result_checks.items() if not passed]
    if failed:
        summary_bits.append(f"failed_checks={'; '.join(failed)}")
    if notes:
        summary_bits.append(f"notes={'; '.join(notes)}")
    return " | ".join(summary_bits)


def main() -> None:
    rows = []
    for task in load_tasks():
        result = score_task(task)
        checks = result.checks
        row = {
            "task_id": task["task_id"],
            "failure_dimension": task["failure_dimension"],
            "source_mode": task["source_mode"],
            "partition": task.get("partition", "dev"),
            "suggested_required_claims": int(checks.get("required_claims_present", False)),
            "suggested_forbidden_claims": int(checks.get("forbidden_claims_absent", False)),
            "suggested_expected_action": int(checks.get("expected_action_present", False)),
            "suggested_dimension_guardrail": int(any(v for k, v in checks.items() if k not in {
                "required_claims_present",
                "forbidden_claims_absent",
                "expected_action_present",
                "allowed_evidence_only",
            })),
            "suggested_allowed_evidence_only": int(checks.get("allowed_evidence_only", False)),
            "avg_score": result.score,
            "passed": int(result.passed),
            "candidate_output": task.get("candidate_output", ""),
            "reasoning_summary": build_reasoning(task, checks, result.notes),
        }
        rows.append(row)

    fieldnames = [
        "task_id",
        "failure_dimension",
        "source_mode",
        "partition",
        "suggested_required_claims",
        "suggested_forbidden_claims",
        "suggested_expected_action",
        "suggested_dimension_guardrail",
        "suggested_allowed_evidence_only",
        "avg_score",
        "passed",
        "candidate_output",
        "reasoning_summary",
    ]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(OUT_CSV)


if __name__ == "__main__":
    main()
