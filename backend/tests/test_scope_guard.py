import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.scope_guard import (
    DEFAULT_REFUSAL_MESSAGE,
    ScopeDecision,
    check_scope,
    classify_scope_llm,
    evaluate_scope_deterministic,
)


def test_deterministic_in_scope_software_tasks():
    in_scope_prompts = [
        "Build an API that retrieves Toyota car prices.",
        "How do I fix a null pointer exception in Java?",
        "Explain how async/await works in Python with an example.",
        "Write a Dockerfile for a Next.js application.",
        "How to optimize PostgreSQL query with indexing?",
        "Create a REST endpoint using FastAPI to upload CSV files.",
        "Refactor this function to reduce time complexity.",
        "How do I prevent SQL injection in my login endpoint?",
        "Explain buffer overflow vulnerability in C code.",
        "Review this regular expression for ReDoS risks.",
        "```python\ndef add(a, b):\n    return a + b\n```\nWhat does this do?",
        "Traceback (most recent call last):\n  File 'main.py', line 10\nTypeError: unsupported operand",
    ]

    for p in in_scope_prompts:
        decision = evaluate_scope_deterministic(p)
        assert decision is not None, f"Expected deterministic decision for: {p}"
        assert decision.allowed is True, f"Expected allowed=True for: {p}"
        assert decision.method == "deterministic_allow"


def test_deterministic_out_of_scope_prompts():
    out_of_scope_prompts = [
        "What is the price of a Toyota Fortuner?",
        "How to bake a chocolate cake at home?",
        "What are the symptoms of the common flu?",
        "Who is the president of France?",
        "Write a love poem about the ocean.",
        "Who won the 2022 FIFA World Cup?",
        "Should I buy Tesla stock today?",
        "Horoscope for Scorpio today",
        "",
        "   ",
    ]

    for p in out_of_scope_prompts:
        decision = evaluate_scope_deterministic(p)
        assert decision is not None, f"Expected deterministic decision for: {p}"
        assert decision.allowed is False, f"Expected allowed=False for: {p}"
        assert decision.method == "deterministic_reject"
        assert decision.refusal_message is not None


def test_llm_classifier_ambiguous_allowed():
    async def run():
        mock_choice = MagicMock()
        mock_choice.message.content = '{"allowed": true, "reason": "Software conceptual inquiry"}'
        mock_response = MagicMock(choices=[mock_choice])

        with patch("app.services.scope_guard.AsyncOpenAI") as mock_openai_cls:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_cls.return_value = mock_client

            with patch("app.services.scope_guard.get_settings") as mock_settings:
                mock_settings.return_value.omniroute_api_key = "test-key"
                mock_settings.return_value.omniroute_base_url = "http://localhost:20128/v1"
                mock_settings.return_value.normal_assistant_model = "auto/best-coding"

                decision = await classify_scope_llm("Can you explain how trees work?")
                assert decision.allowed is True
                assert decision.method == "llm_classifier"
                assert mock_client.chat.completions.create.call_count == 1

    asyncio.run(run())


def test_llm_classifier_ambiguous_rejected():
    async def run():
        mock_choice = MagicMock()
        mock_choice.message.content = '{"allowed": false, "reason": "General gardening advice"}'
        mock_response = MagicMock(choices=[mock_choice])

        with patch("app.services.scope_guard.AsyncOpenAI") as mock_openai_cls:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_cls.return_value = mock_client

            with patch("app.services.scope_guard.get_settings") as mock_settings:
                mock_settings.return_value.omniroute_api_key = "test-key"
                mock_settings.return_value.omniroute_base_url = "http://localhost:20128/v1"
                mock_settings.return_value.normal_assistant_model = "auto/best-coding"

                decision = await classify_scope_llm("How to prune apple trees?")
                assert decision.allowed is False
                assert decision.method == "llm_classifier"
                assert decision.refusal_message == DEFAULT_REFUSAL_MESSAGE
                assert mock_client.chat.completions.create.call_count == 1

    asyncio.run(run())


def test_llm_classifier_error_fallback_allows():
    async def run():
        with patch("app.services.scope_guard.AsyncOpenAI") as mock_openai_cls:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("API error"))
            mock_openai_cls.return_value = mock_client

            with patch("app.services.scope_guard.get_settings") as mock_settings:
                mock_settings.return_value.omniroute_api_key = "test-key"
                mock_settings.return_value.omniroute_base_url = "http://localhost:20128/v1"
                mock_settings.return_value.normal_assistant_model = "auto/best-coding"

                decision = await classify_scope_llm("Vague prompt")
                assert decision.allowed is True
                assert decision.method == "llm_classifier"

    asyncio.run(run())

