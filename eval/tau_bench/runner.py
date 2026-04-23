from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from agent.config import get_settings


@dataclass
class TauBenchRunSummary:
    run_label: str
    domain: str
    model_name: str
    pass_at_1_mean: float | None
    confidence_interval_95: list[float] | None
    cost_usd: float | None
    p50_latency_ms: int | None
    p95_latency_ms: int | None
    status: str
    notes: str


@dataclass
class TauBenchTrajectory:
    run_label: str
    trial_index: int
    task_id: str | None
    trajectory_status: str
    trace_ref: str | None
    notes: str


class TauBenchRunner:
    """File-contract scaffold for tau2-bench runs."""

    def __init__(self, score_output_path: Path, trace_output_path: Path) -> None:
        self.score_output_path = score_output_path
        self.trace_output_path = trace_output_path
        self.score_output_path.parent.mkdir(parents=True, exist_ok=True)
        self.trace_output_path.parent.mkdir(parents=True, exist_ok=True)

    def write_placeholder_suite(self) -> list[TauBenchRunSummary]:
        summaries = [
            TauBenchRunSummary(
                run_label="dev_baseline",
                domain="retail",
                model_name="pending_pinned_model",
                pass_at_1_mean=None,
                confidence_interval_95=None,
                cost_usd=None,
                p50_latency_ms=None,
                p95_latency_ms=None,
                status="not_run",
                notes="Awaiting real tau2-bench execution against the pinned dev-tier model.",
            ),
            TauBenchRunSummary(
                run_label="reproduction_check",
                domain="retail",
                model_name="pending_pinned_model",
                pass_at_1_mean=None,
                confidence_interval_95=None,
                cost_usd=None,
                p50_latency_ms=None,
                p95_latency_ms=None,
                status="not_run",
                notes="Keep this entry for the required reproduction check once real runs are available.",
            ),
        ]
        trajectories = [
            TauBenchTrajectory(
                run_label="dev_baseline",
                trial_index=0,
                task_id=None,
                trajectory_status="placeholder_only",
                trace_ref=None,
                notes="Replace with full dev-trial trajectories after running tau2-bench.",
            ),
            TauBenchTrajectory(
                run_label="reproduction_check",
                trial_index=0,
                task_id=None,
                trajectory_status="placeholder_only",
                trace_ref=None,
                notes="Replace with full dev-trial trajectories after running tau2-bench.",
            ),
        ]
        self._write_score_log(summaries)
        self._write_trace_log(trajectories)
        return summaries

    def _write_score_log(self, summaries: list[TauBenchRunSummary]) -> None:
        self.score_output_path.write_text(
            json.dumps([summary.__dict__ for summary in summaries], indent=2),
            encoding="utf-8",
        )

    def _write_trace_log(self, trajectories: list[TauBenchTrajectory]) -> None:
        with self.trace_output_path.open("w", encoding="utf-8") as handle:
            for trajectory in trajectories:
                handle.write(json.dumps(trajectory.__dict__) + "\n")


def main() -> None:
    settings = get_settings()
    runner = TauBenchRunner(
        score_output_path=settings.resolved_score_output_path,
        trace_output_path=settings.project_root / "eval" / "trace_log.jsonl",
    )
    summaries = runner.write_placeholder_suite()
    print(json.dumps([summary.__dict__ for summary in summaries], indent=2))


if __name__ == "__main__":
    main()
