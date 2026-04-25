from __future__ import annotations

import json
import math
from statistics import median, quantiles
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
    """File-contract helper for tau2-bench runs and imported trajectories."""

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

    def write_score_from_trace_log(
        self,
        *,
        model_name: str = "pinned_dev_tier_model",
        git_commit: str | None = None,
        reproduction_simulation_count: int = 15,
    ) -> list[dict]:
        """Derive auditable score entries from an existing tau2 trace JSONL file."""
        rows = self._read_completed_trajectories()
        if not rows:
            raise ValueError(f"No completed tau2 trajectories found in {self.trace_output_path}")

        baseline = self._summarize_rows(
            rows,
            run_label="dev_baseline",
            model_name=model_name,
            git_commit=git_commit,
            notes="Full 5-trial dev-slice baseline derived from eval/trace_log.jsonl.",
        )
        reproduction_rows = rows[:reproduction_simulation_count]
        reproduction = self._summarize_rows(
            reproduction_rows,
            run_label="reproduction_check",
            model_name=model_name,
            git_commit=git_commit,
            notes=(
                f"Small-scale reproduction check from the first {reproduction_simulation_count} "
                "completed trajectories in eval/trace_log.jsonl."
            ),
        )
        summaries = [baseline, reproduction]
        self.score_output_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
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

    def _read_completed_trajectories(self) -> list[dict]:
        rows: list[dict] = []
        if not self.trace_output_path.exists():
            return rows
        for line in self.trace_output_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if "reward" in payload and "task_id" in payload:
                rows.append(payload)
        return rows

    def _summarize_rows(
        self,
        rows: list[dict],
        *,
        run_label: str,
        model_name: str,
        git_commit: str | None,
        notes: str,
    ) -> dict:
        rewards = [float(row["reward"]) for row in rows]
        costs = [float(row.get("agent_cost", 0.0) or 0.0) for row in rows]
        durations = [float(row.get("duration", 0.0) or 0.0) for row in rows]
        task_ids = {str(row["task_id"]) for row in rows}
        pass_at_1 = sum(rewards) / len(rewards)
        low, high = self._wilson_ci(sum(rewards), len(rewards))
        return {
            "run_label": run_label,
            "domain": rows[0].get("domain", "retail"),
            "model_name": model_name,
            "evaluated_simulations": len(rows),
            "total_tasks": len(task_ids),
            "num_trials": round(len(rows) / len(task_ids), 4) if task_ids else None,
            "pass_at_1": round(pass_at_1, 4),
            "pass_at_1_ci_95": [round(low, 4), round(high, 4)],
            "avg_agent_cost": round(sum(costs) / len(costs), 4),
            "p50_latency_seconds": round(median(durations), 4),
            "p95_latency_seconds": round(self._percentile(durations, 95), 4),
            "infra_error_count": sum(1 for row in rows if row.get("termination_reason") == "infra_error"),
            "trace_ref": self._display_trace_ref(),
            "git_commit": git_commit,
            "status": "completed",
            "notes": notes,
        }

    def _wilson_ci(self, successes: float, total: int) -> tuple[float, float]:
        if total == 0:
            return (0.0, 0.0)
        z = 1.96
        phat = successes / total
        denominator = 1 + z**2 / total
        centre = phat + z**2 / (2 * total)
        margin = z * math.sqrt((phat * (1 - phat) + z**2 / (4 * total)) / total)
        return ((centre - margin) / denominator, (centre + margin) / denominator)

    def _percentile(self, values: list[float], percentile: int) -> float:
        if len(values) == 1:
            return values[0]
        return quantiles(values, n=100, method="inclusive")[percentile - 1]

    def _display_trace_ref(self) -> str:
        try:
            return self.trace_output_path.resolve().relative_to(Path.cwd()).as_posix()
        except ValueError:
            return self.trace_output_path.as_posix()

    def existing_git_commit(self) -> str | None:
        if not self.score_output_path.exists():
            return None
        try:
            payload = json.loads(self.score_output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        entries = payload if isinstance(payload, list) else [payload]
        for entry in entries:
            if isinstance(entry, dict) and entry.get("git_commit"):
                return str(entry["git_commit"])
        return None


def main() -> None:
    settings = get_settings()
    runner = TauBenchRunner(
        score_output_path=settings.resolved_score_output_path,
        trace_output_path=settings.project_root / "eval" / "trace_log.jsonl",
    )
    if runner.trace_output_path.exists() and runner._read_completed_trajectories():
        summaries = runner.write_score_from_trace_log(git_commit=runner.existing_git_commit())
    else:
        summaries = [summary.__dict__ for summary in runner.write_placeholder_suite()]
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
