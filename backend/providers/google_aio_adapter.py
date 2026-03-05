"""Google AIO adapter.

Google AIO does not currently expose a single stable API for all contexts where
an answer can include first-class citations. This adapter therefore supports:
1) Direct model invocation for generated answer text.
2) Optional citation fallback collection via an auxiliary fetcher (e.g. custom
   search endpoint, site index, or CSE API) configured by environment.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .base import NormalizedResponse, ProviderAdapter, ProviderError, UsageMetrics
from .config import ProviderConfig


class GoogleAIOAdapter(ProviderAdapter):
    provider_name = "google_aio"

    def __init__(
        self,
        config: ProviderConfig,
        client: Callable[[Dict[str, Any]], Dict[str, Any]],
        citation_collector: Optional[Callable[[str, Dict[str, Any]], List[str]]] = None,
    ):
        self.config = config
        self.client = client
        self.citation_collector = citation_collector

    def _build_payload(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "model": context.get("model", self.config.model),
            "prompt": prompt,
            "region": context.get("region", self.config.region),
            "safety": context.get("safety", "default"),
        }

    def _dispatch(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.config.api_key:
            raise ProviderError(
                code="missing_api_key",
                message="GOOGLE_AIO_API_KEY is not configured",
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
        text = raw_response.get("output_text", "")
        if not text:
            raise ProviderError(
                code="invalid_response",
                message="No output_text returned from Google AIO",
                provider=self.provider_name,
                details={"raw_response": raw_response},
            )

        citations = raw_response.get("citations") or []
        if not citations and self.citation_collector:
            citations = self.citation_collector(text, context)

        usage_raw = raw_response.get("usage", {})
        usage = UsageMetrics(
            input_tokens=usage_raw.get("input_tokens"),
            output_tokens=usage_raw.get("output_tokens"),
            total_tokens=usage_raw.get("total_tokens"),
        )

        integration_path = {
            "direct": "Use Google AIO model endpoint for answer generation.",
            "fallback": (
                "When citations are absent, run configured collector "
                f"({self.config.extra.get('collection_fallback', 'google-cse')}) "
                "against answer text and attach top URLs."
            ),
        }

        return NormalizedResponse(
            provider=self.provider_name,
            model=raw_response.get("model", context.get("model", self.config.model)),
            raw_text=text,
            citations=citations,
            answer={"type": "text_with_optional_sources", "content": text},
            latency_ms=latency_ms,
            usage=usage,
            metadata={"integration_path": integration_path},
        )
