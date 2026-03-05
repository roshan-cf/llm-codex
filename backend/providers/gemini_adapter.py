"""Gemini provider adapter implementation."""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from .base import NormalizedResponse, ProviderAdapter, ProviderError, UsageMetrics
from .config import ProviderConfig


class GeminiAdapter(ProviderAdapter):
    provider_name = "gemini"

    def __init__(self, config: ProviderConfig, client: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.config = config
        self.client = client

    def _build_payload(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "model": context.get("model", self.config.model),
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": context.get("temperature", 0.2)},
        }

    def _dispatch(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.config.api_key:
            raise ProviderError(
                code="missing_api_key",
                message="GEMINI_API_KEY is not configured",
                provider=self.provider_name,
            )
        return self.client(payload)

    def _normalize(
        self,
        raw_response: Dict[str, Any],
        *,
        latency_ms: float,
        context: Dict[str, Any],
    ) -> NormalizedResponse:
        candidates = raw_response.get("candidates") or []
        if not candidates:
            raise ProviderError(
                code="invalid_response",
                message="No candidates returned from Gemini",
                provider=self.provider_name,
                details={"raw_response": raw_response},
            )

        parts: List[Dict[str, Any]] = candidates[0].get("content", {}).get("parts", [])
        text = "\n".join(part.get("text", "") for part in parts if part.get("text"))
        grounding = candidates[0].get("groundingMetadata", {})
        citations = [
            support.get("uri")
            for support in grounding.get("groundingChunks", [])
            if support.get("uri")
        ]

        usage_raw = raw_response.get("usageMetadata", {})
        usage = UsageMetrics(
            input_tokens=usage_raw.get("promptTokenCount"),
            output_tokens=usage_raw.get("candidatesTokenCount"),
            total_tokens=usage_raw.get("totalTokenCount"),
        )

        return NormalizedResponse(
            provider=self.provider_name,
            model=raw_response.get("modelVersion", context.get("model", self.config.model)),
            raw_text=text,
            citations=citations,
            answer={"type": "multimodal_text", "content": text},
            latency_ms=latency_ms,
            usage=usage,
            metadata={"safety_ratings": candidates[0].get("safetyRatings", [])},
        )
