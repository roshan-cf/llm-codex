"""Configuration primitives for provider adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from backend.secrets import EnvManager, KeyVault, NullKeyVault


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


def _resolve_api_key(
    *,
    env: EnvManager,
    key_vault: KeyVault,
    api_key_env: str,
    api_key_ref_env: str,
) -> Optional[str]:
    direct = env.get(api_key_env)
    if direct:
        return direct

    secret_ref = env.get(api_key_ref_env)
    if not secret_ref:
        return None
    return key_vault.get_secret(secret_ref)


def from_env(
    env_manager: Optional[EnvManager] = None,
    key_vault: Optional[KeyVault] = None,
) -> AdapterConfigRegistry:
    """Build configuration from environment variables and optional key vault refs.

    Supported variables:
      * OPENAI_API_KEY / OPENAI_API_KEY_SECRET_REF, OPENAI_MODEL, OPENAI_RATE_LIMIT_PER_MINUTE
      * PERPLEXITY_API_KEY / PERPLEXITY_API_KEY_SECRET_REF, PERPLEXITY_MODEL,
        PERPLEXITY_RATE_LIMIT_PER_MINUTE
      * GEMINI_API_KEY / GEMINI_API_KEY_SECRET_REF, GEMINI_MODEL, GEMINI_REGION,
        GEMINI_RATE_LIMIT_PER_MINUTE
      * GOOGLE_AIO_API_KEY / GOOGLE_AIO_API_KEY_SECRET_REF, GOOGLE_AIO_MODEL,
        GOOGLE_AIO_REGION, GOOGLE_AIO_RATE_LIMIT_PER_MINUTE
    """

    env = env_manager or EnvManager.from_os()
    vault = key_vault or NullKeyVault()

    def int_env(name: str, default: int) -> int:
        try:
            return int(env.get(name, str(default)) or default)
        except ValueError:
            return default

    providers = {
        "chatgpt": ProviderConfig(
            provider_name="chatgpt",
            api_key=_resolve_api_key(
                env=env,
                key_vault=vault,
                api_key_env="OPENAI_API_KEY",
                api_key_ref_env="OPENAI_API_KEY_SECRET_REF",
            ),
            model=env.get("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
            rate_limit_per_minute=int_env("OPENAI_RATE_LIMIT_PER_MINUTE", 60),
            region=env.get("OPENAI_REGION"),
        ),
        "perplexity": ProviderConfig(
            provider_name="perplexity",
            api_key=_resolve_api_key(
                env=env,
                key_vault=vault,
                api_key_env="PERPLEXITY_API_KEY",
                api_key_ref_env="PERPLEXITY_API_KEY_SECRET_REF",
            ),
            model=env.get("PERPLEXITY_MODEL", "sonar-pro") or "sonar-pro",
            rate_limit_per_minute=int_env("PERPLEXITY_RATE_LIMIT_PER_MINUTE", 30),
            region=env.get("PERPLEXITY_REGION"),
        ),
        "gemini": ProviderConfig(
            provider_name="gemini",
            api_key=_resolve_api_key(
                env=env,
                key_vault=vault,
                api_key_env="GEMINI_API_KEY",
                api_key_ref_env="GEMINI_API_KEY_SECRET_REF",
            ),
            model=env.get("GEMINI_MODEL", "gemini-1.5-pro") or "gemini-1.5-pro",
            rate_limit_per_minute=int_env("GEMINI_RATE_LIMIT_PER_MINUTE", 60),
            region=env.get("GEMINI_REGION", "us-central1"),
        ),
        "google_aio": ProviderConfig(
            provider_name="google_aio",
            api_key=_resolve_api_key(
                env=env,
                key_vault=vault,
                api_key_env="GOOGLE_AIO_API_KEY",
                api_key_ref_env="GOOGLE_AIO_API_KEY_SECRET_REF",
            ),
            model=env.get("GOOGLE_AIO_MODEL", "gemini-1.5-flash") or "gemini-1.5-flash",
            rate_limit_per_minute=int_env("GOOGLE_AIO_RATE_LIMIT_PER_MINUTE", 60),
            region=env.get("GOOGLE_AIO_REGION", "global"),
            extra={
                "collection_fallback": env.get("GOOGLE_AIO_COLLECTION_FALLBACK", "google-cse")
                or "google-cse"
            },
        ),
    }
    return AdapterConfigRegistry(providers=providers)
