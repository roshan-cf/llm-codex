from backend.api.analysis import AnalysisAPI, CreateAnalysisRunRequest
from backend.providers.base import NormalizedResponse, ProviderAdapter
from backend.providers.orchestrator import ProviderOrchestrator


class StubAdapter(ProviderAdapter):
    provider_name = "stub"

    def _build_payload(self, prompt, context):
        return {"prompt": prompt, "context": context}

    def _dispatch(self, payload, context):
        return {
            "text": f"Answer for {payload['prompt']} about {payload['context']['domain']} see https://example.com [1]",
            "citations": ["https://example.com"],
        }

    def _normalize(self, raw_response, *, latency_ms, context):
        return NormalizedResponse(
            provider=self.provider_name,
            model="stub-model",
            raw_text=raw_response["text"],
            citations=raw_response["citations"],
            answer={"content": raw_response["text"]},
            latency_ms=latency_ms,
        )


def _api() -> AnalysisAPI:
    orchestrator = ProviderOrchestrator(adapters={"stub": StubAdapter()})
    return AnalysisAPI(orchestrator=orchestrator)


def test_post_run_creates_scored_run_with_expected_frontend_fields():
    api = _api()

    run = api.post_run(
        CreateAnalysisRunRequest(
            url="https://Acme.com/some/path",
            provider="stub",
            prompt="Best CRM for startups?",
            brand_name="Acme",
            brand_terms=["Acme"],
            topic_terms=["CRM", "startup"],
            competitors=["rival.com"],
        )
    )

    assert run["domain"] == "acme.com"
    assert run["provider"] == "stub"
    assert run["prompt"] == "Best CRM for startups?"
    assert isinstance(run["visibility"], float)
    assert isinstance(run["quality"], float)
    assert run["citations"] == ["https://example.com"]
    assert "rawOutput" in run
    assert run["status"] == "completed"
    assert run["createdAt"]
    assert run["updatedAt"]
    assert run["completedAt"]


def test_get_runs_and_get_run_return_dashboard_read_models():
    api = _api()
    first = api.post_run(CreateAnalysisRunRequest(url="https://a.com", provider="stub", prompt="p1"))
    second = api.post_run(CreateAnalysisRunRequest(url="https://b.com", provider="stub", prompt="p2"))

    runs = api.get_runs()

    assert [run["id"] for run in runs] == [second["id"], first["id"]]
    assert api.get_run(first["id"])["id"] == first["id"]


def test_post_run_rejects_invalid_url_hostname():
    api = _api()

    try:
        api.post_run(CreateAnalysisRunRequest(url="not-a-domain", provider="stub", prompt="test"))
    except ValueError as err:
        assert "primary domain must be a valid hostname" in str(err)
    else:
        raise AssertionError("expected ValueError")
