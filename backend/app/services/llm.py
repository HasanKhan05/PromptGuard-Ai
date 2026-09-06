from openai import AsyncOpenAI

from ..config import get_settings

SYSTEM_PROMPT = (
    "You are PromptGuard Ai, a dedicated software development assistant. "
    "Provide clear, concise, and practical assistance with programming, debugging, "
    "code review, code explanation, software architecture, development tools, "
    "and software engineering concepts across any domain. "
    "Keep responses focused on software engineering and development."
)


def get_client() -> AsyncOpenAI:
    settings = get_settings()
    if not settings.omniroute_api_key:
        raise RuntimeError("OMNIROUTE_API_KEY is not configured in backend/.env")
    return AsyncOpenAI(
        base_url=settings.omniroute_base_url,
        api_key=settings.omniroute_api_key,
    )


async def create_chat_stream(prompt: str, requested_model: str | None = None):
    settings = get_settings()
    model = requested_model or settings.normal_assistant_model
    client = get_client()
    stream = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=settings.normal_temperature,
        max_tokens=settings.normal_max_output_tokens,
        stream=True,
    )
    return model, stream
