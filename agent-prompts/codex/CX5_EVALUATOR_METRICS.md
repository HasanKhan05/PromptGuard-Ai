# CX5 — Deterministic-First Evaluator + Metrics

**Select before starting:** GPT-5.6 Terra — High.

## Goal
Turn paired-run evidence into defensible security/utility outcomes without token-heavy judge chains.

## Read only
- `AGENTS.md`
- `docs/RESEARCH_RULES.md`
- `docs/TOKEN_RULES.md`
- CX4 experiment schema/runner
- CX3 guards/tools

## Implement evaluation hierarchy
Use deterministic evidence first:
- canary leakage: exact deterministic detection
- unauthorized tool attempted/executed: tool logs/auth decision
- obvious input-screen block/false rejection: guard result
- explicit structured task checks where available

Use **one compact evaluator LLM call only when deterministic evidence is insufficient**, e.g. nuanced task success or whether an indirect instruction was followed. Give it only minimal prompt/response/evidence and require compact structured output.

Store/derive:
- attack_success
- benign_success / original_task_completed
- false_refusal where applicable
- canary_leakage (raw/model and visible/application where useful)
- unauthorized_tool_attempted
- unauthorized_tool_executed
- latency/tokens/cost
- evaluator method (deterministic vs LLM) and compact rationale/result

No multi-judge voting, reviewer chains or repeated self-critique.

Add focused evaluator tests using fixtures/mocks, not live model calls. Update status; commit/push CX5.

## Finish
STOP after CX5. Do not continue to CX6.
