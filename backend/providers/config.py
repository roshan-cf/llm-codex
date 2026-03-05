"""Configuration primitives for provider adapters."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(slots=True)
class ProviderConfig:
    provider_name: str
    api_key: Optional[str]
    model: str
    rate_limit_per_minute: int = 60
    region: Optional[str] = None
    extra: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class AdapterConfigRegistry:
    """Container for provider-level runtime configuration."""

    providers: Dict[str, ProviderConfig]

    def for_provider(self, provider_name: str) -> ProviderConfig:
        if provider_name not in self.providers:
            raise KeyError(f"No config registered for provider '{provider_name}'")
        return self.providers[provider_name]


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def from_env() -> AdapterConfigRegistry:
    """Build configuration from environment variables.

    Supported variables:
      * OPENAI_API_KEY, OPENAI_MODEL, OPENAI_RATE_LIMIT_PER_MINUTE
      * PERPLEXITY_API_KEY, PERPLEXITY_MODEL, PERPLEXITY_RATE_LIMIT_PER_MINUTE
      * GEMINI_API_KEY, GEMINI_MODEL, GEMINI_REGION, GEMINI_RATE_LIMIT_PER_MINUTE
      * GOOGLE_AIO_API_KEY, GOOGLE_AIO_MODEL, GOOGLE_AIO_REGION,
        GOOGLE_AIO_RATE_LIMIT_PER_MINUTE
    """

    def int_env(name: str, default: int) -> int:
        try:
            return int(_env(name, str(default)) or default)
        except ValueError:
            return default

    providers = {
        "chatgpt": ProviderConfig(
            provider_name="chatgpt",
            api_key=_env("OPENAI_API_KEY"),
            model=_env("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
            rate_limit_per_minute=int_env("OPENAI_RATE_LIMIT_PER_MINUTE", 60),
            region=_env("OPENAI_REGION"),
        ),
        "perplexity": ProviderConfig(
            provider_name="perplexity",
            api_key=_env("PERPLEXITY_API_KEY"),
            model=_env("PERPLEXITY_MODEL", "sonar-pro") or "sonar-pro",
            rate_limit_per_minute=int_env("PERPLEXITY_RATE_LIMIT_PER_MINUTE", 30),
            region=_env("PERPLEXITY_REGION"),
        ),
        "gemini": ProviderConfig(
            provider_name="gemini",
            api_key=_env("GEMINI_API_KEY"),
            model=_env("GEMINI_MODEL", "gemini-1.5-pro") or "gemini-1.5-pro",
            rate_limit_per_minute=int_env("GEMINI_RATE_LIMIT_PER_MINUTE", 60),
            region=_env("GEMINI_REGION", "us-central1"),
        ),
        "google_aio": ProviderConfig(
            provider_name="google_aio",
            api_key=_env("GOOGLE_AIO_API_KEY"),
            model=_env("GOOGLE_AIO_MODEL", "gemini-1.5-flash") or "gemini-1.5-flash",
            rate_limit_per_minute=int_env("GOOGLE_AIO_RATE_LIMIT_PER_MINUTE", 60),
            region=_env("GOOGLE_AIO_REGION", "global"),
            extra={
                "collection_fallback": _env("GOOGLE_AIO_COLLECTION_FALLBACK", "google-cse")
                or "google-cse"
            },
        ),
    }
    return AdapterConfigRegistry(providers=providers)
