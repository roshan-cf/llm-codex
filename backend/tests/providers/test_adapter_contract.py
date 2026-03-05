import pytest

from backend.providers import (
    ChatGPTAdapter,
    GeminiAdapter,
    GoogleAIOAdapter,
    PerplexityAdapter,
    ProviderConfig,
    ProviderError,
)


def _config(name: str) -> ProviderConfig:
    return ProviderConfig(provider_name=name, api_key="test-key", model="test-model")


@pytest.mark.parametrize(
    "adapter_cls,provider_name,fixture_name",
    [
        (ChatGPTAdapter, "chatgpt", "chatgpt_raw_response"),
        (PerplexityAdapter, "perplexity", "perplexity_raw_response"),
        (GeminiAdapter, "gemini", "gemini_raw_response"),
    ],
)
def test_adapter_execute_contract(adapter_cls, provider_name, fixture_name, request):
    raw = request.getfixturevalue(fixture_name)
    adapter = adapter_cls(_config(provider_name), client=lambda _: raw)

    result = adapter.execute("hello", {"trace_id": "t-1"})

    assert result.provider == provider_name
    assert isinstance(result.raw_text, str) and result.raw_text
    assert isinstance(result.citations, list)
    assert isinstance(result.answer, dict)
    assert result.latency_ms >= 0


def test_google_aio_adapter_uses_citation_fallback(google_aio_raw_response):
    adapter = GoogleAIOAdapter(
        _config("google_aio"),
        client=lambda _: google_aio_raw_response,
        citation_collector=lambda text, _context: [f"https://collector.example?q={text}"],
    )

    result = adapter.execute("hello", {})

    assert result.provider == "google_aio"
    assert result.citations == ["https://collector.example?q=Google AIO answer."]
    assert "integration_path" in result.metadata


def test_missing_key_raises_unified_error(chatgpt_raw_response):
    adapter = ChatGPTAdapter(
        ProviderConfig(provider_name="chatgpt", api_key=None, model="gpt-4o-mini"),
        client=lambda _: chatgpt_raw_response,
    )

    with pytest.raises(ProviderError) as exc_info:
        adapter.execute("hello")

    assert exc_info.value.code == "missing_api_key"
    assert exc_info.value.provider == "chatgpt"
