# HX7 — Wire Real Research APIs into Final Figma UI (Antigravity)

**Owner:** Antigravity

**Select before starting:** Gemini 3.7 Flash — Medium.

## Goal
Connect the already-finalized visual frontend to the real CX2–CX6 APIs without redesigning it.

## Read only
- `AGENTS.md`
- `docs/DESIGN_REFERENCE.md`
- `docs/IMPLEMENTATION_STATUS.md`
- frontend API/types/components/pages involved in Assistant/Experiments/Benchmarks/Research
- backend API schemas only as needed

## Implement/wire
- normal Assistant remains real `/api/chat`
- after response, eligibility data comes from `/api/attacks/eligibility`
- selected card calls `/api/attacks/generate`
- generated attack is editable/regeneratable/restorable
- Run Paired Experiment calls `/api/experiments/run`
- experiment page/result cards show real baseline/defended responses and metrics
- Benchmarks page uses `/api/benchmarks`
- Research page uses `/api/research`

Preserve finalized navigation/design. Remove mock/illustrative values from **live research state**, but it is acceptable to show a clearly labeled empty/preview state before real experiments exist.

Keep frontend API code simple; no global state library unless genuinely necessary (it should not be).

Run frontend build/check + targeted integration tests. Update status; commit/push CX7.

## Finish
STOP after CX7. Do not continue to CX8.
