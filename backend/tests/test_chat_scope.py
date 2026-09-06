import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.services.scope_guard import DEFAULT_REFUSAL_MESSAGE


def test_chat_out_of_scope_rejection_streaming():
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"prompt": "What is the price of a Toyota Fortuner?"},
        )
    assert response.status_code == 200
    assert response.headers["X-PromptGuard-Scope"] == "out_of_scope"
    assert response.headers["X-PromptGuard-Scope-Method"] == "deterministic_reject"
    assert DEFAULT_REFUSAL_MESSAGE in response.text


def test_chat_in_scope_passes_to_stream():
    async def mock_stream_gen():
        chunk = MagicMock()
        chunk.model = "auto/best-coding"
        chunk.choices = [MagicMock(delta=MagicMock(content="Here is the API code."))]
        yield chunk

    with patch("app.routers.chat.create_chat_stream", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = ("auto/best-coding", mock_stream_gen())

        with TestClient(app) as client:
            response = client.post(
                "/api/chat",
                json={"prompt": "Build an API that retrieves Toyota car prices."},
            )
        assert response.status_code == 200
        assert response.headers["X-PromptGuard-Scope"] == "in_scope"
        assert response.headers["X-PromptGuard-Scope-Method"] == "deterministic_allow"
        assert "Here is the API code." in response.text
