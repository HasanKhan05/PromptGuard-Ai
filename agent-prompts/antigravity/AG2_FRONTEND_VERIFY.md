# AG2 — Frontend Install, Build and Visual Sanity

**Select before starting:** Gemini 3.7 Flash — Medium.

## Goal
Verify the supplied Figma-aligned frontend actually installs, builds and renders. **Do not redesign it.**

## Read only
- `AGENTS.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/DESIGN_REFERENCE.md`
- `frontend/package.json`
- then only frontend files implicated by build/lint/runtime errors

## Execute
1. Work only inside `frontend/` plus status docs.
2. Create `frontend/.env.local` from its example if absent; no secrets are needed there.
3. Install dependencies.
4. Run the project's lint/check command and production build. If the configured lint command is incompatible with the installed Next.js version, make the **smallest modern equivalent change** rather than downgrading/redesigning.
5. Start the frontend and inspect the four routes/pages: Assistant, Experiments, Benchmarks, Research.
6. Confirm logo/navigation/layout render and no obvious runtime console error exists.
7. Preserve illustrative benchmark/research numbers and their preview labeling; do not make them “real”.
8. Fix only actual build/runtime/obvious visual breakage. Do not rewrite CSS/component architecture for style.
9. Update implementation status.
10. Make one phase commit and push if origin is configured.

## Do not
- touch FastAPI/SQLite/OmniRoute implementation
- implement research endpoints
- redesign against your own taste
- install a UI framework just to replace working supplied components
- spend time on perfect mobile production behavior; basic responsiveness already exists

## Verification
- frontend dev server starts
- Assistant/Experiments/Benchmarks/Research routes render
- lint/check passes
- production build passes

## Finish
STOP after AG2 and report concise completed/changed/tests/blocker/commit. Do not continue to AG3.
