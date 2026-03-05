"""Base provider adapter interfaces and normalized response contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class ProviderError(Exception):
    """Unified provider error schema used by all adapters."""

    code: str
    message: str
    provider: str
    retryable: bool = False
    status_code: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"{self.provider}::{self.code} - {self.message} "
            f"(retryable={self.retryable}, status={self.status_code})"
        )


@dataclass(slots=True)
class UsageMetrics:
    """Token usage metrics if a provider reports them."""

    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


@dataclass(slots=True)
class NormalizedResponse:
    """Cross-provider normalized response schema."""

    provider: str
    model: Optional[str]
    raw_text: str
    citations: List[str]
    answer: Dict[str, Any]
    latency_ms: float
    usage: UsageMetrics = field(default_factory=UsageMetrics)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProviderAdapter(ABC):
    """Base adapter contract for LLM and answer-engine providers."""

    provider_name: str

    def execute(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> NormalizedResponse:
        """Execute against a provider and normalize into `NormalizedResponse`."""
        payload = self._build_payload(prompt, context or {})
        start = perf_counter()
        try:
            raw_response = self._dispatch(payload, context or {})
        except ProviderError:
            raise
        except Exception as exc:  # pragma: no cover - defensive guard
            raise ProviderError(
                code="provider_dispatch_error",
                message=str(exc),
                provider=self.provider_name,
                retryable=True,
                details={"payload": payload},
            ) from exc

        latency_ms = (perf_counter() - start) * 1000
        return self._normalize(raw_response, latency_ms=latency_ms, context=context or {})

    @abstractmethod
    def _build_payload(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build provider-specific request payload."""

    @abstractmethod
    def _dispatch(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform provider call and return the raw response dictionary."""

    @abstractmethod
    def _normalize(
        self,
        raw_response: Dict[str, Any],
        *,
        latency_ms: float,
        context: Dict[str, Any],
    ) -> NormalizedResponse:
        """Normalize a raw provider response to `NormalizedResponse`."""
