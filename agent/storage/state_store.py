from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.models.schemas import CompetitorGapBrief, ConversationState, HiringSignalBrief, LeadRecord
from agent.utils.serialization import write_json


class FileStateStore:
    """Persists lead and conversation snapshots to local JSON files."""

    def __init__(self, runtime_dir: Path, project_root: Path) -> None:
        self.runtime_root = runtime_dir
        self.project_root = project_root
        self.state_dir = runtime_dir / "state"
        self.briefs_dir = runtime_dir / "briefs"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.briefs_dir.mkdir(parents=True, exist_ok=True)

    def save(self, lead: LeadRecord, conversation: ConversationState) -> str:
        target = self.state_dir / f"{lead.lead_id}.json"
        write_json(
            target,
            {
                "lead": lead,
                "conversation": conversation,
            },
        )
        return str(target)

    def save_briefs(
        self,
        lead: LeadRecord,
        hiring_signal_brief: HiringSignalBrief,
        competitor_gap_brief: CompetitorGapBrief,
    ) -> dict[str, str]:
        hiring_target = self.briefs_dir / f"{lead.lead_id}_hiring_signal.json"
        competitor_target = self.briefs_dir / f"{lead.lead_id}_competitor_gap.json"
        write_json(hiring_target, hiring_signal_brief)
        write_json(competitor_target, competitor_gap_brief)
        return {
            "hiring_signal": str(hiring_target),
            "competitor_gap": str(competitor_target),
        }

    def save_current_run_manifest(
        self,
        lead: LeadRecord,
        artifact_paths: dict[str, str | Path | None],
    ) -> str:
        target = self.runtime_root / "current-run.json"
        write_json(
            target,
            {
                "lead_id": lead.lead_id,
                "generated_at": datetime.now(timezone.utc),
                "artifacts": {
                    key: self._to_visualization_relative(value) for key, value in artifact_paths.items()
                },
            },
        )
        return str(target)

    def _to_visualization_relative(self, value: str | Path | None) -> str | None:
        if value is None:
            return None
        path = Path(value)
        if not path.is_absolute():
            path = self.project_root / path
        try:
            relative = path.relative_to(self.project_root).as_posix()
            return f"../{relative}"
        except ValueError:
            return path.as_posix()
