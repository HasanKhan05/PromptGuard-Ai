# Hybrid Execution Plan – Antigravity / Codex

## Completed Antigravity phases
- **AG1** – Git/GitHub bootstrap – **GPT‑OSS 120B** – ✅
- **AG2** – Frontend install & build – **Gemini 3.7 Flash** – ✅
- **AG3** – FastAPI + OmniRoute verification – **GPT‑OSS 120B** – ✅
- **AG4** – End‑to‑end streaming integration – **Gemini 3.8 Flash** – ✅
- **AG5** – Minimal SQLite persistence – **Gemini 3.6 Flash** – ✅
- **AG6** – Independent foundation audit – **Claude Sonnet 4.6** – ✅

## Current repository checkpoint
- **Commit hash:** `69c062f`
- **Git status:** clean, `main` up‑to‑date with `origin/main`

## New hybrid phase ownership & model allocation
| Phase | Owner | Model | Reason / Level |
|------|-------|-------|----------------|
| **CX1** | Antigravity | Gemini 3.7 Flash (Medium) | Assistant role + deterministic scope guard |
| **CX2** | Codex | GPT‑5.6 Terra (High) | Attack eligibility + generation |
| **CX3** | Codex | GPT‑5.6 Terra (High) | Four defenses + harmless tools |
| **CX4** | Codex | GPT‑5.6 Sol (High) | Paired‑experiment engine + evidence schema |
| **CX5** | Antigravity | Claude Sonnet 4.6 (Thinking) | Evaluator + metrics |
| **CX6** | Antigravity | Gemini 3.6 Flash (Medium) | Benchmark aggregation + research backend |
| **CX7** | Antigravity | Gemini 3.7 Flash (Medium) | Connect real research APIs to finalized frontend |
| **CX8** | Antigravity | Claude Sonnet 4.6 (Thinking) | Final scientific/security audit |

- **CX0** is removed – its responsibilities are covered by AG6.
- **CX7 fallback** to Gemini 3.8 Flash (High) only if genuine integration difficulty arises.
- **Claude Opus** remains emergency‑only and must not be used by default.

## Agent switching rules (mandatory)
1. **One agent at a time** – Antigravity and Codex never edit the repo simultaneously.
2. A phase must finish **all tests, commit, push**, and leave a clean tree before the next agent takes over.
3. The next agent starts from the exact Git checkpoint left by the previous agent.
4. No redesign of already‑verified components unless a concrete correctness issue is found.
5. Keep token usage low – only the listed model per phase, no extra LLM calls.

## Codex quota‑conservation strategy
- Reserve remaining Codex quota for **CX4** (critical scientific implementation) and any genuine bugs discovered later.
- Use cheaper Luna/Terra models for routine work; upgrade only on focused blocker‑only rescues.

---
*This document supersedes any previous phase‑order description. All agents must consult `docs/HYBRID_EXECUTION_PLAN.md` for the authoritative ownership and model schedule.*
