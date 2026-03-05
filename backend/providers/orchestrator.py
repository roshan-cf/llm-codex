"""Provider orchestration with circuit-breakers, fallback routing, and observability."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Dict, Optional

from backend.observability import Observability

from .base import NormalizedResponse, ProviderAdapter, ProviderError


@dataclass(slots=True)
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout_s: float = 30.0
    failures: int = 0
    opened_at: Optional[float] = None

    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if monotonic() - self.opened_at >= self.recovery_timeout_s:
            self.failures = 0
            self.opened_at = None
            return False
        return True

    def on_success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def on_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = monotonic()


@dataclass(slots=True)
class ProviderOrchestrator:
    adapters: Dict[str, ProviderAdapter]
    fallback_order: Dict[str, list[str]] = field(default_factory=dict)
    observability: Observability = field(default_factory=Observability)
    _breakers: Dict[str, CircuitBreaker] = field(default_factory=dict)

    def _breaker(self, provider: str) -> CircuitBreaker:
        if provider not in self._breakers:
            self._breakers[provider] = CircuitBreaker()
        return self._breakers[provider]

    def execute(
        self,
        provider: str,
        prompt: str,
        context: Optional[dict] = None,
    ) -> NormalizedResponse:
        candidates = [provider, *(self.fallback_order.get(provider, []))]
        errors: list[ProviderError] = []

        for candidate in candidates:
            adapter = self.adapters.get(candidate)
            if not adapter:
                continue

            breaker = self._breaker(candidate)
            if breaker.is_open():
                errors.append(
                    ProviderError(
                        code="circuit_open",
                        message=f"Circuit breaker open for {candidate}",
                        provider=candidate,
                        retryable=True,
                    )
                )
                continue

            try:
                response = adapter.execute(prompt, context=context)
                breaker.on_success()
                self.observability.record_provider_latency(candidate, response.latency_ms)
                self.observability.record_run(success=True)
                return response
            except ProviderError as err:
                errors.append(err)
                breaker.on_failure()
                self.observability.record_run(success=False)

        last_error = errors[-1] if errors else None
        raise ProviderError(
            code="provider_fallback_exhausted",
            message="All provider attempts failed",
            provider=provider,
            retryable=True,
            details={
                "attempted": candidates,
                "errors": [str(error) for error in errors],
                "last_error": str(last_error) if last_error else None,
            },
        )
