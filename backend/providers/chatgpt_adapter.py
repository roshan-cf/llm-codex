"""ChatGPT provider adapter implementation."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from .base import NormalizedResponse, ProviderAdapter, ProviderError, UsageMetrics
from .config import ProviderConfig


class ChatGPTAdapter(ProviderAdapter):
    provider_name = "chatgpt"

    def __init__(self, config: ProviderConfig, client: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.config = config
        self.client = client

    def _build_payload(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "model": context.get("model", self.config.model),
            "messages": [
                {"role": "system", "content": context.get("system_prompt", "You are helpful.")},
                {"role": "user", "content": prompt},
            ],
            "temperature": context.get("temperature", 0.2),
        }

    def _dispatch(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.config.api_key:
            raise ProviderError(
                code="missing_api_key",
                message="OPENAI_API_KEY is not configured",
                provider=self.provider_name,
                retryable=False,
            )
        return self.client(payload)

    def _normalize(
        self,
        raw_response: Dict[str, Any],
        *,
        latency_ms: float,
        context: Dict[str, Any],
    ) -> NormalizedResponse:
        choices = raw_response.get("choices") or []
        if not choices:
            raise ProviderError(
                code="invalid_response",
                message="No choices returned from ChatGPT",
                provider=self.provider_name,
                details={"raw_response": raw_response},
            )

        message = choices[0].get("message", {})
        text = message.get("content", "")
        usage_raw = raw_response.get("usage", {})
        usage = UsageMetrics(
            input_tokens=usage_raw.get("prompt_tokens"),
            output_tokens=usage_raw.get("completion_tokens"),
            total_tokens=usage_raw.get("total_tokens"),
        )

        return NormalizedResponse(
            provider=self.provider_name,
            model=raw_response.get("model", context.get("model", self.config.model)),
            raw_text=text,
            citations=[],
            answer={"type": "text", "content": text},
            latency_ms=latency_ms,
            usage=usage,
            metadata={"id": raw_response.get("id")},
        )
