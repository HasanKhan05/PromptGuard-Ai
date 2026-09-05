# File Map — Read Less, Work Faster

Agents should use this map instead of scanning the whole repository.

## Always-light context
- `AGENTS.md` — hard project rules
- `docs/IMPLEMENTATION_STATUS.md` — current durable state

## Product/research context
- `docs/PROJECT_SPEC.md`
- `docs/RESEARCH_RULES.md`
- `docs/ARCHITECTURE.md`
- `docs/TOKEN_RULES.md`

## Frontend
- `frontend/app/`
- `frontend/components/`
- `frontend/lib/`
- `frontend/public/promptguard-logo.png`
- `frontend/app/globals.css`
- `docs/DESIGN_REFERENCE.md`

## Backend foundation
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/db.py`
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/routers/`
- `backend/app/services/`
- `backend/tests/`

## Scripts
- `scripts/`

## Phase prompts
- `agent-prompts/antigravity/`
- `agent-prompts/codex/`

Read a file outside the current phase only when an error or dependency directly requires it.
