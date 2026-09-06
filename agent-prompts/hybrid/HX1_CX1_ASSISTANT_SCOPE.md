# HX1 — Assistant Control Layer + Scope Guard (Antigravity)

**Owner:** Antigravity

**Select before starting:** Gemini 3.7 Flash — Medium.

## Goal
Finalize compact normal developer-assistant behavior and a simple application scope guard without overengineering.

## Read only
- `AGENTS.md`
- `docs/PROJECT_SPEC.md`
- `docs/TOKEN_RULES.md`
- `backend/app/services/llm.py`
- `backend/app/routers/chat.py`
- `backend/app/schemas.py`
- tests relevant to chat/scope

## Execute
1. Finalize a concise software-development-assistant system role.
2. Implement a lightweight scope/domain guard that rejects clearly unrelated requests while allowing software tasks about any domain.
   - "What is the price of a Toyota Fortuner?" → out of scope.
   - "Build an API that retrieves Toyota car prices." → allowed.
3. Prefer deterministic/cheap logic for obvious cases. If an LLM ambiguity check is used, it must be compact and only for genuinely ambiguous prompts; do not create a multi-call classifier chain.
4. Keep `/api/chat` a real live model response path.
5. Keep normal routing compatible with OmniRoute auto routing.
6. Add focused tests for clear in-scope/out-of-scope examples.
7. Update status and commit/push CX1.

## Do not
Implement research attack logic/defenses yet. The scope guard is ordinary application behavior, not a research defense.

## Finish
STOP after CX1. Do not continue to CX2.
