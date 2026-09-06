from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openai import APIError

from ..config import get_settings
from ..db import SessionLocal
from ..models import ChatRun
from ..schemas import ChatRequest
from ..services.llm import create_chat_stream
from ..services.scope_guard import DEFAULT_REFUSAL_MESSAGE, check_scope

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat(payload: ChatRequest):
    settings = get_settings()
    requested_model = payload.model or settings.normal_assistant_model

    # Normal application scope/domain guard
    scope_decision = await check_scope(payload.prompt)
    if not scope_decision.allowed:
        refusal = scope_decision.refusal_message or DEFAULT_REFUSAL_MESSAGE

        async def refusal_body():
            yield refusal
            db = SessionLocal()
            try:
                db.add(
                    ChatRun(
                        prompt=payload.prompt,
                        response=refusal,
                        requested_model=requested_model,
                        actual_model="scope_guard",
                    )
                )
                db.commit()
            finally:
                db.close()

        return StreamingResponse(
            refusal_body(),
            media_type="text/plain; charset=utf-8",
            headers={
                "X-PromptGuard-Requested-Model": requested_model,
                "X-PromptGuard-Scope": "out_of_scope",
                "X-PromptGuard-Scope-Method": scope_decision.method,
            },
        )

    try:
        requested_model, stream = await create_chat_stream(payload.prompt, payload.model)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"OmniRoute/model request failed: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Unable to start model stream: {exc}") from exc

    async def body():
        parts: list[str] = []
        actual_model: str | None = None
        try:
            async for chunk in stream:
                actual_model = getattr(chunk, "model", actual_model)
                if not chunk.choices:
                    continue
                text = chunk.choices[0].delta.content or ""
                if text:
                    parts.append(text)
                    yield text
        finally:
            if parts:
                db = SessionLocal()
                try:
                    db.add(
                        ChatRun(
                            prompt=payload.prompt,
                            response="".join(parts),
                            requested_model=requested_model,
                            actual_model=actual_model,
                        )
                    )
                    db.commit()
                finally:
                    db.close()

    return StreamingResponse(
        body(),
        media_type="text/plain; charset=utf-8",
        headers={
            "X-PromptGuard-Requested-Model": requested_model,
            "X-PromptGuard-Scope": "in_scope",
            "X-PromptGuard-Scope-Method": scope_decision.method,
        },
    )
