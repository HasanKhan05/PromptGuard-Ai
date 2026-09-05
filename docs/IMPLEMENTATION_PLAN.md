# Optimized Implementation Plan

## Why phases are model-specific
The user manually switches models between phases. Each phase is sized so that work of roughly similar reasoning difficulty is performed under one selected model, then the agent must stop. This avoids wasting high-tier quota on routine setup and allows the user/ChatGPT to rebalance usage after every reply.

# Stage A — Antigravity foundation

## AG1 — Git/GitHub + secret-safe bootstrap
Model: GPT-OSS 120B / Medium.
No application implementation.

## AG2 — Frontend verification
Model: Gemini 3.7 Flash / Medium.
Install/run/build supplied Figma-aligned frontend; fix actual frontend issues only.

## AG3 — FastAPI + OmniRoute backend verification
Model: GPT-OSS 120B / Medium.
Set up Python environment, health route, backend streaming route, verify direct Gemini and Pollinations calls through backend.

## AG4 — End-to-end streaming integration
Model: Gemini 3.8 Flash / High.
Run browser + backend + OmniRoute together and fix only integration/streaming/loading/error problems.

## AG5 — Minimal SQLite + targeted tests
Model: Gemini 3.6 Flash / Medium.
Verify minimal persistence and tests; no research schema.

## AG6 — Independent foundation audit
Model: Claude Sonnet 4.6 / Thinking.
Full foundation verification, minimal fixes, commit/push, update handoff status. STOP.

# Stage C — Codex research/security engine

## CX0 — Antigravity handoff audit
Model: GPT-5.6 Luna / Medium.
Verify repo status and foundation with minimal/no changes.

## CX1 — Assistant control + scope guard
Model: GPT-5.6 Terra / Medium.
Finalize compact developer-assistant role and lightweight scope behavior.

## CX2 — Attack eligibility + generation
Model: GPT-5.6 Terra / High.
Implement one-call eligibility for all four families and selected-family attack transformation.

## CX3 — Four defenses + harmless tools
Model: GPT-5.6 Terra / High.
Implement the four mapped defenses and 2–3 deterministic read-only tools/authorization.

## CX4 — Paired experiment engine + evidence schema
Model: GPT-5.6 Sol / High.
Most research-critical phase: controlled baseline/defended runner and exact evidence logging.

## CX5 — Evaluator + metrics
Model: GPT-5.6 Terra / High.
Deterministic-first evaluation, optional compact LLM judge only where required.

## CX6 — Benchmark aggregation + research backend
Model: GPT-5.6 Luna / Medium.
SQLite/Python aggregation, benchmark API, compact research interpretation API.

## CX7 — Real research frontend wiring
Model: GPT-5.6 Terra / Medium.
Replace illustrative/live mocks with actual API state while preserving finalized visual design.

## CX8 — Final scientific/security audit
Model: GPT-5.6 Sol / High.
Validate fairness, metrics, no fake results/canned responses, runtime token discipline, full build/tests. STOP.

See `PHASE_LAUNCHERS.md` for exact launchers and `agent-prompts/` for phase contracts.
