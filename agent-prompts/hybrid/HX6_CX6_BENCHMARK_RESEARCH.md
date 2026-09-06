# HX6 — Benchmark Aggregation + Research Backend (Antigravity)

**Owner:** Antigravity

**Select before starting:** Gemini 3.6 Flash — Medium.

## Goal
Use cheap deterministic Python/SQLite work to aggregate stored experiments and expose concise research data.

## Read only
- `AGENTS.md`
- `docs/RESEARCH_RULES.md`
- `docs/TOKEN_RULES.md`
- experiment/evaluation models from CX4/CX5
- current API schemas/routers

## Implement
Endpoints:
- `GET /api/benchmarks`
- `GET /api/runs/{id}`
- `GET /api/research`

Benchmarks:
- calculate counts/percentages from stored runs in Python/SQL/optionally pandas
- overall and per-family attack success before/after matching defense
- benign success / false refusal
- leakage/tool metrics where relevant
- latency/token/cost summaries
- never hardcode final research percentages

Research endpoint:
- derive graphs/findings from aggregate data
- deterministic templated findings are preferred when sufficient
- if an LLM is used for a short “Research Answer”, send only compact aggregate metrics and cap output; no raw transcripts
- make only data-supported claims
- handle “not enough experiments yet” honestly

## Do not
Run the full benchmark automatically. Add aggregation tests with small fixture data.

## Finish
STOP after CX6. Do not continue to CX7.
