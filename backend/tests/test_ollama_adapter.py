"""Tests for Ollama experiment provider adapter and provider routing."""
import asyncio
from unittest.mock import AsyncMock, patch
import pytest

from app.services.ollama import (
    clean_ollama_model_name,
    get_ollama_client,
    is_ollama_model,
    OllamaChatCompletion,
    OllamaClient,
)
from app.services.experiments import get_experiment_client


def test_is_ollama_model():
    # Ollama models
    assert is_ollama_model("llama2:7b") is True
    assert is_ollama_model("llama2") is True
    assert is_ollama_model("ollama/llama2:7b") is True
    assert is_ollama_model("ollama:llama2:7b") is True
    assert is_ollama_model("gemma2:9b") is True
    assert is_ollama_model("gemma3:12b") is True
    assert is_ollama_model("llama3:8b") is True

    # OmniRoute / Gemini models
    assert is_ollama_model("gemini/gemini-3.1-flash-lite") is False
    assert is_ollama_model("auto/best-coding") is False
    assert is_ollama_model("gpt-4o") is False


def test_clean_ollama_model_name():
    assert clean_ollama_model_name("llama2:7b") == "llama2:7b"
    assert clean_ollama_model_name("ollama/llama2:7b") == "llama2:7b"
    assert clean_ollama_model_name("ollama:llama2:7b") == "llama2:7b"
    assert clean_ollama_model_name("  ollama/llama2:7b  ") == "llama2:7b"


def test_get_experiment_client_dispatch():
    ollama_client = get_experiment_client("llama2:7b")
    assert isinstance(ollama_client, OllamaClient)

    ollama_client_prefix = get_experiment_client("ollama/llama2:7b")
    assert isinstance(ollama_client_prefix, OllamaClient)

    # Gemini model dispatches to OpenAI client
    omni_client = get_experiment_client("gemini/gemini-3.1-flash-lite")
    assert not isinstance(omni_client, OllamaClient)


def test_ollama_create_mock():
    async def _run():
        mock_response_data = {
            "model": "llama2:7b",
            "created_at": "2026-09-08T07:00:00.000Z",
            "message": {"role": "assistant", "content": "I am Llama 2."},
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 45,
            "eval_count": 12,
        }

        from unittest.mock import MagicMock
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response_data

        client = get_ollama_client(base_url="http://localhost:11434")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            result = await client.chat.completions.create(
                model="ollama/llama2:7b",
                messages=[
                    {"role": "system", "content": "You are an assistant."},
                    {"role": "user", "content": "Hello"},
                ],
                temperature=0.2,
                max_tokens=800,
                tools=[{"type": "function", "function": {"name": "test"}}],  # Tools should be stripped
            )

            assert isinstance(result, OllamaChatCompletion)
            assert result.choices[0].message.content == "I am Llama 2."
            assert result.choices[0].message.role == "assistant"
            assert result.choices[0].message.tool_calls is None
            assert result.usage.prompt_tokens == 45
            assert result.usage.completion_tokens == 12
            assert result.usage.total_tokens == 57
            assert result.model == "llama2:7b"

            # Verify POST payload sent to Ollama
            call_kwargs = mock_post.call_args.kwargs
            payload = call_kwargs["json"]
            assert payload["model"] == "llama2:7b"
            assert payload["options"]["temperature"] == 0.2
            assert payload["options"]["num_predict"] == 800
            assert payload["options"]["num_ctx"] == 4096
            assert "tools" not in payload  # Ensure tools were stripped

    asyncio.run(_run())
