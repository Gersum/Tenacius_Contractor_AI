from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FORBIDDEN_STYLE_TERMS = {
    "a-player",
    "a players",
    "bench",
    "cheap",
    "offshore",
    "outsourcing vendor",
    "rockstar",
    "ninja",
    "just checking in",
    "hope you're well",
    "revolutionizing",
}

# Calibration note for the deterministic layer:
# - a score near 1.0 means the candidate satisfies every mechanical rubric item
# - a score around 0.8 means one item failed but the row still clears the current pass threshold
# - a score around 0.5 means the task is only partially compliant and should be treated as a miss
# Judge-only dimensions remain reserved for a later phase and are not silently applied here.


@dataclass(frozen=True)
class ScoreResult:
    task_id: str
    score: float
    passed: bool
    checks: dict[str, bool]
    notes: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "score": self.score,
            "passed": self.passed,
            "checks": self.checks,
            "notes": self.notes,
        }


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def contains_any(text: str, phrases: list[str] | set[str]) -> bool:
    haystack = normalize(text)
    return any(normalize(phrase) in haystack for phrase in phrases if phrase)


def contains_all(text: str, phrases: list[str]) -> bool:
    haystack = normalize(text)
    return all(normalize(phrase) in haystack for phrase in phrases if phrase)


def validate_task(task: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if "task_id" not in task:
        errors.append("missing task_id")
    if "ground_truth" not in task:
        errors.append("missing ground_truth")
        return errors
    ground_truth = task["ground_truth"]
    for key in ("required_claims", "forbidden_claims", "expected_action"):
        if key not in ground_truth:
            errors.append(f"missing ground_truth.{key}")
    if "failure_dimension" not in task:
        errors.append("missing failure_dimension")
    return errors


def score_task(task: dict[str, Any], candidate_output: str | None = None) -> ScoreResult:
    errors = validate_task(task)
    if errors:
        return ScoreResult(
            task_id=str(task.get("task_id", "unknown")),
            score=0.0,
            passed=False,
            checks={"task_schema_valid": False},
            notes=errors,
        )

    try:
        output = candidate_output if candidate_output is not None else task["candidate_output"]
    except KeyError:
        return ScoreResult(
            task_id=str(task.get("task_id", "unknown")),
            score=0.0,
            passed=False,
            checks={"candidate_output_present": False},
            notes=["missing candidate_output"],
        )

    if not isinstance(output, str) or not output.strip():
        return ScoreResult(
            task_id=str(task.get("task_id", "unknown")),
            score=0.0,
            passed=False,
            checks={"candidate_output_present": False},
            notes=["empty or non-string candidate_output"],
        )

    output_norm = normalize(output)
    ground_truth = task["ground_truth"]
    dimension = task["failure_dimension"]

    checks: dict[str, bool] = {}
    notes: list[str] = []

    checks["required_claims_present"] = contains_all(output, ground_truth["required_claims"])
    checks["forbidden_claims_absent"] = not contains_any(output, ground_truth["forbidden_claims"])
    checks["expected_action_present"] = normalize(ground_truth["expected_action"]) in output_norm
    checks["allowed_evidence_only"] = not any(marker in output_norm for marker in ("all your peers", "everyone", "guaranteed"))

    if dimension == "tone_style_drift":
        checks["style_terms_absent"] = not contains_any(output, FORBIDDEN_STYLE_TERMS)
    elif dimension == "bench_overcommitment":
        bench = task["input"].get("bench_summary_excerpt", {})
        requested = int(bench.get("requested_engineers", 1))
        available = int(bench.get("available_engineers", 0))
        checks["capacity_guardrail_respected"] = available >= requested or contains_any(
            output, ["phased", "available", "route to a human", "capacity"]
        )
    elif dimension == "scheduling_handoff_correctness":
        checks["utc_or_overlap_present"] = contains_any(output, ["utc", "overlap", "3 to 5", "1 to 2"])
    elif dimension == "hiring_signal_overclaiming":
        checks["weak_signal_softened"] = not contains_any(output, ["aggressive scaling", "rapid hiring", "definitely"])
    elif dimension == "competitor_gap_overclaiming":
        checks["gap_language_softened"] = not contains_any(output, ["falling behind", "lack", "all your peers"])
    elif dimension == "public_signal_reliability":
        checks["source_uncertainty_respected"] = contains_any(output, ["public signal", "source", "appears", "not confirm"])
    elif dimension == "icp_misclassification":
        checks["segment_uncertainty_respected"] = contains_any(output, ["abstain", "unknown", "low confidence", "exploratory"])
    else:
        checks["known_failure_dimension"] = False

    passed_count = sum(1 for passed in checks.values() if passed)
    score = round(passed_count / len(checks), 4)
    for name, passed in checks.items():
        if not passed:
            notes.append(f"Failed {name}")

    return ScoreResult(task_id=task["task_id"], score=score, passed=score >= 0.8, checks=checks, notes=notes)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Score Tenacious-Bench tasks deterministically.")
    parser.add_argument("task_file", type=Path, help="A JSONL task file or a single JSON task.")
    parser.add_argument("--candidate-output", type=Path, help="Optional text file overriding candidate_output.")
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    args = parser.parse_args()

    candidate = args.candidate_output.read_text(encoding="utf-8") if args.candidate_output else None
    if args.task_file.suffix == ".jsonl":
        results = [score_task(task, candidate).as_dict() for task in load_jsonl(args.task_file)]
    else:
        results = [score_task(json.loads(args.task_file.read_text(encoding="utf-8")), candidate).as_dict()]

    payload: dict[str, Any] = {
        "task_count": len(results),
        "pass_rate": round(sum(1 for result in results if result["passed"]) / len(results), 4) if results else 0,
        "avg_score": round(sum(result["score"] for result in results) / len(results), 4) if results else 0,
        "results": results,
    }
    text = json.dumps(payload, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
