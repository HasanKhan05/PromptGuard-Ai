# AG4 — End-to-End Streaming Integration

**Select before starting:** Gemini 3.8 Flash — High.

## Goal
Prove the real path works end-to-end:
`Browser → Next.js → FastAPI → OmniRoute → model → streamed browser response`.

This is the most integration-sensitive Antigravity phase, so use the stronger Gemini model but keep scope narrow.

## Read only
- `AGENTS.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/ARCHITECTURE.md`
- `frontend/lib/api.ts`
- `frontend/app/page.tsx`
- `frontend/components/PromptComposer.tsx`
- `backend/app/routers/chat.py`
- `backend/app/services/llm.py`
- config/CORS files only if an integration error points there

## Execute
1. Start OmniRoute (assume user-managed), FastAPI and frontend.
2. Send one short real coding prompt from the Assistant UI.
3. Confirm response text arrives progressively or correctly through the existing streaming path.
4. Confirm loading and error states recover cleanly.
5. Confirm the frontend never receives/exposes the OmniRoute API key.
6. If browser cancellation already exists, verify it; do not build elaborate cancellation infrastructure if absent and not needed.
7. Fix only end-to-end integration issues (CORS, stream decoding, endpoint mismatch, UI state, backend stream errors).
8. Re-run one short successful end-to-end test after fixes.
9. Update status; commit/push AG4.

## Do not
- implement attack eligibility or experiment workflow backend
- redesign UI
- add WebSockets if HTTP streaming already works
- introduce proxy services/microservices
- repeatedly generate long model responses

## Escalation
If a genuine streaming bug remains after one focused fix attempt, STOP with exact error and relevant files. Do not burn repeated High turns; ChatGPT may switch the rescue to Claude Sonnet Thinking.

## Finish
STOP after AG4. Concise report only. Do not continue to AG5.
