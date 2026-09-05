# CX0 — Codex Handoff Audit

**Select before starting:** GPT-5.6 Luna — Medium.

## Goal
Cheaply verify Antigravity left a clean working foundation before spending Terra/Sol quota.

## Read only
- `AGENTS.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/IMPLEMENTATION_PLAN.md`
- recent `git log --oneline`

Inspect source only if a verification command fails.

## Execute
1. Confirm branch/remote/status and AG6 handoff commit.
2. Confirm no secrets/runtime DB are tracked.
3. Run targeted foundation verification commands already documented/scripts.
4. Confirm `/health`, frontend build and backend tests are healthy (do not run unnecessary live LLM calls if AG6 already recorded successful routes and nothing changed).
5. Fix only a trivial handoff defect if obvious; otherwise report blocker instead of spending Luna on complex debugging.
6. Update status: `CX0 complete / CX1 next` and commit only if a real file change was required.

## Do not
Implement research features yet or refactor foundation code.

## Finish
STOP. Concise report. Do not continue to CX1.
