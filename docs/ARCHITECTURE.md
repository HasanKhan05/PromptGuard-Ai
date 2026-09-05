# Architecture — Intentionally Small

```text
Next.js / React UI
       |
       | HTTP + streaming
       v
FastAPI backend
       |
       | OpenAI-compatible API
       v
OmniRoute on localhost:20128/v1
       |
       +--> Gemini connections
       +--> Pollinations
       +--> other routes only if already configured/needed

SQLite = local experiment evidence + metrics
```

## Frontend
- Next.js App Router, React, TypeScript
- existing Tailwind/CSS design implementation
- Lucide Icons, React Markdown
- native fetch/ReadableStream
- no secret keys

## Backend
- FastAPI + Pydantic
- SQLAlchemy + local SQLite
- OpenAI-compatible async client
- pytest
- pandas only when benchmark aggregation needs it

## OmniRoute
Base URL: `http://localhost:20128/v1`

Normal assistant default: `auto/best-coding`.
Verified direct routes include:
- `gemini/gemini-3.1-flash-lite`
- `gemini/gemini-3-flash-preview`
- `pol/qwen-coder`

Controlled paired tests use fixed `EXPERIMENT_MODEL`, never auto routing.

## Data evolution
Antigravity keeps only minimal `chat_runs` persistence. Codex CX4 introduces the smallest research schema that supports reproducible paired experiments. Do not pre-build a large schema.
