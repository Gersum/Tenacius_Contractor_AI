from __future__ import annotations

import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any
from urllib import error, request


class OpenRouterError(RuntimeError):
    """Raised when an OpenRouter request fails or returns invalid data."""


@dataclass
class OpenRouterChatResult:
    content: str
    model: str | None
    response_id: str | None
    latency_ms: int
    cost_usd: float = 0.0
    usage: dict[str, Any] | None = None
    raw_response: dict[str, Any] | None = None


class OpenRouterClient:
    """Small stdlib-only OpenRouter client for grounded outreach generation."""

    def __init__(
        self,
        *,
        api_key: str,
        app_name: str,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "",
        timeout_seconds: int = 30,
    ) -> None:
        self.api_key = api_key
        self.app_name = app_name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def create_chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_completion_tokens: int = 350,
        response_format: dict[str, Any] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> OpenRouterChatResult:
        payload: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_completion_tokens,
        }
        if self.model:
            payload["model"] = self.model
        if response_format is not None:
            payload["response_format"] = response_format
        if metadata:
            payload["metadata"] = metadata

        req = request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-Title": self.app_name,
            },
            method="POST",
        )

        started = perf_counter()
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise OpenRouterError(
                f"OpenRouter returned HTTP {exc.code}: {body[:240]}"
            ) from exc
        except error.URLError as exc:
            raise OpenRouterError(f"OpenRouter request failed: {exc.reason}") from exc

        latency_ms = int((perf_counter() - started) * 1000)
        try:
            response_json = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise OpenRouterError("OpenRouter returned non-JSON output.") from exc

        choices = response_json.get("choices") or []
        if not choices:
            raise OpenRouterError("OpenRouter response did not contain any choices.")

        message = choices[0].get("message") or {}
        content = self._message_text(message.get("content"))
        if not content:
            raise OpenRouterError("OpenRouter response did not contain message content.")

        return OpenRouterChatResult(
            content=content,
            model=response_json.get("model"),
            response_id=response_json.get("id"),
            latency_ms=latency_ms,
            cost_usd=self._extract_cost(response_json),
            usage=response_json.get("usage"),
            raw_response=response_json,
        )

    def _message_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_value = item.get("text")
                    if isinstance(text_value, str):
                        text_parts.append(text_value)
            return "\n".join(part for part in text_parts if part).strip()
        return ""

    def _extract_cost(self, response_json: dict[str, Any]) -> float:
        usage = response_json.get("usage")
        if not isinstance(usage, dict):
            return 0.0
        for key in ("cost", "total_cost"):
            value = usage.get(key)
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    continue
        return 0.0
