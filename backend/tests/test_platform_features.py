from backend.audit import AuditLogger
from backend.observability import Observability
from backend.providers.base import NormalizedResponse, ProviderAdapter, ProviderError
from backend.providers.config import from_env
from backend.providers.orchestrator import ProviderOrchestrator
from backend.scoring.engine import ScoringEngine
from backend.secrets import EnvManager


class FakeVault:
    def __init__(self, values):
        self.values = values

    def get_secret(self, secret_ref: str):
        return self.values.get(secret_ref)


class StubAdapter(ProviderAdapter):
    provider_name = "stub"

    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def _build_payload(self, prompt, context):
        return {"prompt": prompt}

    def _dispatch(self, payload, context):
        if self.should_fail:
            raise ProviderError(code="down", message="down", provider=self.provider_name, retryable=True)
        return {"text": payload["prompt"]}

    def _normalize(self, raw_response, *, latency_ms, context):
        return NormalizedResponse(
            provider=self.provider_name,
            model="stub-model",
            raw_text=raw_response["text"],
            citations=[],
            answer={"content": raw_response["text"]},
            latency_ms=latency_ms,
        )


def test_config_uses_key_vault_ref_when_direct_key_missing():
    env = EnvManager(
        {
            "OPENAI_API_KEY_SECRET_REF": "secret/openai",
            "PERPLEXITY_API_KEY": "direct-key",
        }
    )
    registry = from_env(env_manager=env, key_vault=FakeVault({"secret/openai": "vault-key"}))

    assert registry.for_provider("chatgpt").api_key == "vault-key"
    assert registry.for_provider("perplexity").api_key == "direct-key"


def test_orchestrator_circuit_breaker_and_fallback():
    primary = StubAdapter(should_fail=True)
    fallback = StubAdapter(should_fail=False)
    fallback.provider_name = "fallback"

    obs = Observability()
    orchestrator = ProviderOrchestrator(
        adapters={"primary": primary, "fallback": fallback},
        fallback_order={"primary": ["fallback"]},
        observability=obs,
    )

    response = orchestrator.execute("primary", "hello")

    assert response.provider == "fallback"
    assert obs.run_failure == 1
    assert obs.run_success == 1


def test_scoring_observability_and_audit_logs():
    obs = Observability()
    engine = ScoringEngine(observability=obs)
    _ = engine.score(
        prompt_text="Best analytics vendor?",
        response_text="Acme is better than Rival and see https://example.com [1]",
        domains=["acme.com"],
        expected_intent="recommendation",
        brand_name="Acme",
        brand_terms=["Acme"],
        topic_terms=["analytics"],
        competitors=["Rival"],
        prompt_version="v1",
        provider_model="stub",
    )

    audit = AuditLogger()
    audit.log_prompt_edit(actor="alice", prompt_id="p1", changes={"temperature": [0.2, 0.1]})
    audit.log_run_trigger(actor="alice", run_id="r1", provider="chatgpt", prompt_version="v1")
    audit.log_score_recalculation(actor="system", run_id="r1", reason="weights_changed")

    snap = obs.snapshot()
    assert snap["scoring_job_duration_ms"]["count"] == 1
    assert len(audit.events) == 3
