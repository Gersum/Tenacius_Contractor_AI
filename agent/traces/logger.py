from __future__ import annotations

import json
from pathlib import Path

from agent.config import Settings
from agent.models.schemas import TraceRecord
from agent.utils.serialization import to_jsonable

try:  # pragma: no cover - optional dependency for live observability.
    from langfuse import Langfuse
except ImportError:  # pragma: no cover - optional dependency.
    Langfuse = None


class JsonlTraceLogger:
    """JSONL trace sink with optional Langfuse mirroring."""

    def __init__(self, output_path: Path, settings: Settings | None = None) -> None:
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.touch(exist_ok=True)
        self.settings = settings
        self.langfuse = self._build_langfuse_client(settings)

    def log(self, record: TraceRecord) -> str:
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(to_jsonable(record)) + "\n")
        self._log_to_langfuse(record)
        return record.trace_id

    def _build_langfuse_client(self, settings: Settings | None):
        if settings is None or Langfuse is None:
            return None
        if not (settings.langfuse_public_key and settings.langfuse_secret_key and settings.langfuse_host):
            return None
        try:
            return Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )
        except Exception:
            return None

    def _log_to_langfuse(self, record: TraceRecord) -> None:
        if self.langfuse is None:
            return
        try:
            trace_id = self.langfuse.create_trace_id(seed=record.lead_id)
            parent_span_id = "0123456789abcdef"
            with self.langfuse.start_as_current_observation(
                as_type="span",
                name=record.step_name,
                trace_context={
                    "trace_id": trace_id,
                    "parent_span_id": parent_span_id,
                },
                input={
                    "lead_id": record.lead_id,
                    "conversation_id": record.conversation_id,
                    "inputs_ref": record.inputs_ref,
                    "source_refs": record.source_refs,
                },
                output={
                    "outputs_ref": record.outputs_ref,
                    "status": record.status,
                    "metadata": record.metadata,
                },
                metadata={
                    "prompt_version": record.prompt_version,
                    "model_name": record.model_name,
                    "cost_usd": record.cost_usd,
                    "trace_id": record.trace_id,
                },
                level="ERROR" if record.status != "ok" else "DEFAULT",
                status_message=record.metadata.get("error_message") if isinstance(record.metadata, dict) else None,
            ) as span:
                span.update(
                    end_time=record.finished_at,
                    start_time=record.started_at,
                    metadata={
                        "latency_ms": record.latency_ms,
                        "tool_calls": record.tool_calls,
                        **(record.metadata if isinstance(record.metadata, dict) else {}),
                    },
                )
            self.langfuse.flush()
        except Exception:
            # Observability must never break the pipeline path.
            return
