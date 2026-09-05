# AG6 — Independent Foundation Audit + Codex Handoff

**Select before starting:** Claude Sonnet 4.6 — Thinking.

## Goal
Use one strong cross-model review to verify the Antigravity foundation before Codex takes over. This is an audit/fix phase, **not** a feature phase.

## Read first
- `AGENTS.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/TOKEN_RULES.md`

Then inspect only files needed by failed checks.

## Execute
1. Inspect `git status`, recent phase commits and secret safety.
2. Run full foundation verification:
   - backend tests
   - health endpoint
   - frontend lint/check
   - frontend production build
   - one short end-to-end live chat through frontend/backend/OmniRoute
   - one short Gemini route test
   - one short Pollinations route test
   - SQLite initialization/persistence sanity
3. Confirm frontend navigation/design has not been rewritten.
4. Confirm no research/security features from CX1+ were accidentally implemented.
5. Confirm no unnecessary infrastructure/frameworks were added.
6. Fix only blockers uncovered by these checks; do not refactor healthy code.
7. Update `docs/IMPLEMENTATION_STATUS.md`: mark AG6 complete, set `CX0 next`, record final foundation commit.
8. Commit/push final foundation state.

## Do not
- implement scope guard, attacks, defenses, evaluator, benchmarks or research APIs
- perform a broad architecture rewrite
- use Opus unless ChatGPT later supplies a blocker-only rescue prompt

## Finish / handoff
STOP at the Codex boundary.
Report:
- checks passed
- files changed during audit
- any remaining blocker
- GitHub remote/branch
- final commit hash

Do not continue to CX0.
