from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _read_dotenv() -> dict[str, str]:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value and len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def _env_get(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is not None:
        return raw
    return _read_dotenv().get(name, default)


def _env_get_nonempty(name: str, default: str) -> str:
    raw = _env_get(name, default)
    if raw.strip():
        return raw
    return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        raw = _read_dotenv().get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Application settings with safe outbound defaults."""

    app_name: str = "tenacious-conversion-engine"
    app_env: str = "development"
    sink_mode: bool = True
    live_outbound_enabled: bool = False
    use_seeded_demo_data: bool = False
    default_sdr_email: str = "delivery-lead@example.com"

    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4.1-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openai_api_key: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = ""

    hubspot_access_token: str = ""
    hubspot_portal_id: str = ""

    calcom_base_url: str = "http://127.0.0.1:3001"
    calcom_app_base_url: str = "http://127.0.0.1:3001"
    calcom_api_base_url: str = "http://127.0.0.1:3003"
    calcom_api_key: str = ""
    calcom_event_type_slug: str = ""
    calcom_api_version: str = "2026-02-25"
    calcom_username: str = ""
    calcom_webhook_secret: str = ""
    calcom_booking_start: str = "2026-04-24T11:00:00Z"
    calcom_fallback_enabled: bool = True

    resend_api_key: str = ""
    mailersend_api_key: str = ""

    africastalking_api_key: str = ""
    africastalking_username: str = "sandbox"

    layoffs_csv_path: str = "/Users/gersumasfaw/Downloads/layoffs.csv"
    runtime_artifacts_path: str = "artifacts/runtime"
    trace_output_path: str = "artifacts/traces/agent_trace_log.jsonl"
    score_output_path: str = "eval/score_log.json"

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def resolved_trace_output_path(self) -> Path:
        return self.project_root / self.trace_output_path

    @property
    def resolved_score_output_path(self) -> Path:
        return self.project_root / self.score_output_path

    @property
    def runtime_artifacts_dir(self) -> Path:
        return self.project_root / self.runtime_artifacts_path

    @property
    def outbound_mode(self) -> str:
        if self.sink_mode:
            return "sink"
        if self.live_outbound_enabled:
            return "live"
        return "disabled"

    def assert_safe_runtime(self) -> None:
        if self.sink_mode and self.live_outbound_enabled:
            raise ValueError(
                "Invalid configuration: SINK_MODE and LIVE_OUTBOUND_ENABLED cannot both be true."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings(
        app_name=_env_get("APP_NAME", "tenacious-conversion-engine"),
        app_env=_env_get("APP_ENV", "development"),
        sink_mode=_env_bool("SINK_MODE", True),
        live_outbound_enabled=_env_bool("LIVE_OUTBOUND_ENABLED", False),
        use_seeded_demo_data=_env_bool("USE_SEEDED_DEMO_DATA", False),
        default_sdr_email=_env_get("DEFAULT_SDR_EMAIL", "delivery-lead@example.com"),
        openrouter_api_key=_env_get("OPENROUTER_API_KEY", ""),
        openrouter_model=_env_get_nonempty("OPENROUTER_MODEL", "openai/gpt-4.1-mini"),
        openrouter_base_url=_env_get_nonempty("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        openai_api_key=_env_get("OPENAI_API_KEY", ""),
        langfuse_public_key=_env_get("LANGFUSE_PUBLIC_KEY", ""),
        langfuse_secret_key=_env_get("LANGFUSE_SECRET_KEY", ""),
        langfuse_host=_env_get("LANGFUSE_HOST", ""),
        hubspot_access_token=_env_get("HUBSPOT_ACCESS_TOKEN", ""),
        hubspot_portal_id=_env_get("HUBSPOT_PORTAL_ID", ""),
        calcom_base_url=_env_get_nonempty("CALCOM_BASE_URL", "http://127.0.0.1:3001"),
        calcom_app_base_url=_env_get_nonempty(
            "CALCOM_APP_BASE_URL",
            _env_get_nonempty("CALCOM_BASE_URL", "http://127.0.0.1:3001"),
        ),
        calcom_api_base_url=_env_get_nonempty(
            "CALCOM_API_BASE_URL",
            "http://127.0.0.1:3003",
        ),
        calcom_api_key=_env_get("CALCOM_API_KEY", ""),
        calcom_event_type_slug=_env_get("CALCOM_EVENT_TYPE_SLUG", ""),
        calcom_api_version=_env_get_nonempty("CALCOM_API_VERSION", "2026-02-25"),
        calcom_username=_env_get("CALCOM_USERNAME", ""),
        calcom_webhook_secret=_env_get("CALCOM_WEBHOOK_SECRET", ""),
        calcom_booking_start=_env_get_nonempty("CALCOM_BOOKING_START", "2026-04-24T11:00:00Z"),
        calcom_fallback_enabled=_env_bool("CALCOM_FALLBACK_ENABLED", True),
        resend_api_key=_env_get("RESEND_API_KEY", ""),
        mailersend_api_key=_env_get("MAILERSEND_API_KEY", ""),
        africastalking_api_key=_env_get("AFRICASTALKING_API_KEY", ""),
        africastalking_username=_env_get("AFRICASTALKING_USERNAME", "sandbox"),
        layoffs_csv_path=_env_get("LAYOFFS_CSV_PATH", "/Users/gersumasfaw/Downloads/layoffs.csv"),
        runtime_artifacts_path=_env_get("RUNTIME_ARTIFACTS_PATH", "artifacts/runtime"),
        trace_output_path=_env_get("TRACE_OUTPUT_PATH", "artifacts/traces/agent_trace_log.jsonl"),
        score_output_path=_env_get("SCORE_OUTPUT_PATH", "eval/score_log.json"),
    )
    settings.assert_safe_runtime()
    return settings
