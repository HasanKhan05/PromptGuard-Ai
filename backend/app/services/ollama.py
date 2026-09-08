"""PromptGuard Ai — Ollama local experiment model provider adapter.

Provides a lightweight, OpenAI-compatible chat completion interface to local Ollama
instances (such as llama2:7b) for cross-model security benchmarking.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional
import httpx

from ..config import get_settings


def is_ollama_model(model: str) -> bool:
    """Return True if the model specification targets a local Ollama instance."""
    normalized = model.strip().casefold()
    if normalized.startswith("ollama/") or normalized.startswith("ollama:"):
        return True
    # Standard local model tags and names
    if normalized in {"llama2", "llama2:7b", "llama2:13b", "gemma2:9b", "gemma3:12b"}:
        return True
    if normalized.startswith("llama") or normalized.startswith("gemma"):
        return True
    return False


def clean_ollama_model_name(model: str) -> str:
    """Strip provider prefix if present (e.g. 'ollama/llama2:7b' -> 'llama2:7b')."""
    raw = model.strip()
    if raw.casefold().startswith("ollama/"):
        return raw[len("ollama/"):]
    if raw.casefold().startswith("ollama:"):
        return raw[len("ollama:"):]
    return raw


@dataclass(frozen=True)
class OllamaMessage:
    role: str
    content: str
    tool_calls: Optional[List[Any]] = None


@dataclass(frozen=True)
class OllamaChoice:
    index: int
    message: OllamaMessage
    finish_reason: str = "stop"


@dataclass(frozen=True)
class OllamaUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class OllamaChatCompletion:
    id: str
    object: str
    created: int
    model: str
    choices: List[OllamaChoice]
    usage: OllamaUsage
    system_fingerprint: str = "ollama"
    cost: Optional[float] = None


class OllamaCompletions:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def create(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 800,
        num_ctx: int = 4096,
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> OllamaChatCompletion:
        """Call Ollama /api/chat with options matching the experiment specification.

        Note: Tools are explicitly stripped because models like llama2:7b do not
        support native tool calling, and cross-model comparison excludes tool-dependent cases.
        """
        clean_model = clean_ollama_model_name(model)
        payload = {
            "model": clean_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": num_ctx,
            },
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(360.0, connect=30.0)) as http_client:
            response = await http_client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Ollama API request failed (HTTP {response.status_code}): {response.text}"
                )
            data = response.json()

        content = data.get("message", {}).get("content", "")
        role = data.get("message", {}).get("role", "assistant")
        prompt_tokens = data.get("prompt_eval_count") or 0
        completion_tokens = data.get("eval_count") or 0

        return OllamaChatCompletion(
            id=f"ollama-{data.get('created_at', '')}",
            object="chat.completion",
            created=0,
            model=data.get("model", clean_model),
            choices=[
                OllamaChoice(
                    index=0,
                    message=OllamaMessage(role=role, content=content, tool_calls=None),
                    finish_reason=data.get("done_reason", "stop"),
                )
            ],
            usage=OllamaUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            system_fingerprint="ollama",
            cost=None,
        )


class OllamaChat:
    def __init__(self, base_url: str):
        self.completions = OllamaCompletions(base_url)


class OllamaClient:
    def __init__(self, base_url: str):
        self.chat = OllamaChat(base_url)


def get_ollama_client(base_url: Optional[str] = None) -> OllamaClient:
    """Factory function for OllamaClient using application settings."""
    url = base_url or get_settings().ollama_base_url
    return OllamaClient(base_url=url)
