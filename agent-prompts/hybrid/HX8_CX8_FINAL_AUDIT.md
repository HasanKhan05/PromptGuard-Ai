# HX8 — Final Scientific/Security Audit + Validation (Antigravity)

**Owner:** Antigravity

**Select before starting:** Claude Sonnet 4.6 — Thinking.

## Goal
Perform the final high‑value review. Do not add features. Verify that the project is credible, functional, token‑efficient and scientifically fair for a university portfolio project.

## Read first
- `AGENTS.md`
- `docs/RESEARCH_RULES.md`
- `docs/TOKEN_RULES.md`
- `docs/IMPLEMENTATION_STATUS.md`

## Audit
1. Paired experiment invariant is actually enforced in code/tests.
2. No `auto/...` routing in controlled paired tests.
3. Four attack families and four mapped defenses only; no RAG poisoning overlap.
4. Tool authorization/canary checks are deterministic and safe.
5. LLM evaluator is optional/minimal, not a judge chain.
6. Stored outputs are not served as canned live responses.
7. Benchmarks/research derive from stored actual runs; illustrative values are not presented as final results.
8. Runtime call count/context/output limits follow token rules.
9. No unnecessary production infrastructure/frameworks were introduced.
10. Secrets/runtime DB remain untracked.
11. Frontend preserves final design/navigation.
12. Backend tests, frontend check/build and one short end‑to‑end live test pass.

## Do not
Implement architecture improvements beyond fixing concrete issues.

## Finish
STOP. Report final checks passed, any known limitation, final commit hash, and readiness for benchmark data collection.
