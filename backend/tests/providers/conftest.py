import pytest


@pytest.fixture
def chatgpt_raw_response():
    return {
        "id": "chatcmpl-1",
        "model": "gpt-4o-mini",
        "choices": [{"message": {"content": "ChatGPT says hi."}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


@pytest.fixture
def perplexity_raw_response():
    return {
        "model": "sonar-pro",
        "choices": [{"message": {"content": "Perplexity summary."}}],
        "citations": ["https://example.com/a", "https://example.com/b"],
        "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
    }


@pytest.fixture
def gemini_raw_response():
    return {
        "modelVersion": "gemini-1.5-pro",
        "candidates": [
            {
                "content": {"parts": [{"text": "Gemini answer."}]},
                "groundingMetadata": {
                    "groundingChunks": [{"uri": "https://source.example/gemini"}]
                },
                "safetyRatings": [{"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "probability": "LOW"}],
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 12,
            "candidatesTokenCount": 8,
            "totalTokenCount": 20,
        },
    }


@pytest.fixture
def google_aio_raw_response():
    return {
        "model": "gemini-1.5-flash",
        "output_text": "Google AIO answer.",
        "usage": {"input_tokens": 9, "output_tokens": 6, "total_tokens": 15},
    }
