# Provider Terms of Service (ToS) Compliance by Adapter

This document maps each provider adapter to key operational ToS controls enforced by this codebase.

## Shared controls

- **Credential handling**: API keys are loaded from either direct environment variables or server-side vault references (`*_API_KEY_SECRET_REF`) via `EnvManager` + `KeyVault` integration.
- **Rate-limit respect**: each adapter has `rate_limit_per_minute` in provider config for upstream limiter integration.
- **Auditability**: prompt edits, run triggers, and score recalculations are captured via audit events.
- **Resilience and safety**: orchestration uses circuit breakers and explicit fallback routing to avoid hammering unavailable providers.

## chatgpt (`ChatGPTAdapter`)

- Uses `OPENAI_API_KEY` or `OPENAI_API_KEY_SECRET_REF` and fails closed if missing.
- Sends prompt through role-separated message payload and returns normalized response shape.
- Intended for policy-compliant, non-abusive use under OpenAI API terms.

## perplexity (`PerplexityAdapter`)

- Uses `PERPLEXITY_API_KEY` or `PERPLEXITY_API_KEY_SECRET_REF`; fails closed when absent.
- Requests citations with `return_citations=True` and stores sources in normalized output.
- Designed to preserve attribution/source data expected by answer-engine usage terms.

## gemini (`GeminiAdapter`)

- Uses `GEMINI_API_KEY` or `GEMINI_API_KEY_SECRET_REF`; fails closed when absent.
- Captures grounding URIs and safety metadata from provider response.
- Supports region configuration to align with deployment/data residency requirements.

## google_aio (`GoogleAIOAdapter`)

- Uses `GOOGLE_AIO_API_KEY` or `GOOGLE_AIO_API_KEY_SECRET_REF`; fails closed when absent.
- Supports explicit citation collection fallback path when direct citations are unavailable.
- Includes integration metadata documenting direct and fallback citation behavior for compliance reviews.

## Operational guidance

- Validate your application-specific ToS obligations (end-user disclosures, retention, and data handling) before enabling a provider.
- Keep provider selection and fallback ordering explicit through orchestrator configuration.
- Monitor observability metrics (run failure rate, latency, parse failures) for policy and reliability regressions.
