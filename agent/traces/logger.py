from __future__ import annotations

import json
from pathlib import Path

from agent.models.schemas import TraceRecord
from agent.utils.serialization import to_jsonable


class JsonlTraceLogger:
    """Minimal JSONL trace sink used before Langfuse is wired in."""

    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.touch(exist_ok=True)

    def log(self, record: TraceRecord) -> str:
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(to_jsonable(record)) + "\n")
        return record.trace_id
