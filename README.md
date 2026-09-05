# PromptGuard Ai

PromptGuard Ai is a university-level AI-security research prototype built around a normal software-development assistant. It evaluates four LLM application attack families against four lightweight application-level defenses using controlled paired experiments.

## Important: phased agent workflow
This repository is already prepared for a **model-switching, usage-efficient Antigravity → Codex workflow**.

Do not tell an agent to build the whole project at once.

Start with:
- `START_HERE.txt`
- `PHASE_LAUNCHERS.md`

Detailed phase prompts live under:
- `agent-prompts/antigravity/`
- `agent-prompts/codex/`

## Current supplied foundation
- Final-Figma-aligned Next.js frontend source
- FastAPI foundation
- OmniRoute-compatible streaming chat foundation
- minimal SQLite foundation
- Windows setup/run/test scripts
- env examples and secret-safe gitignore
- compact research/architecture/token rules
- model-specific phase prompts and handoff tracking

## Local endpoints
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Chat: `POST http://localhost:8000/api/chat`
- OmniRoute: `http://localhost:20128/v1`

## Secrets
Copy `backend/.env.example` to `backend/.env` when AG3 asks. Insert the real OmniRoute key locally only. `.env` is ignored by Git.

## Scope
This is deliberately not production SaaS. No unnecessary deployment infrastructure, distributed architecture, complex auth, or framework bloat.
