# AG3 — FastAPI + OmniRoute Backend Verification

**Select before starting:** GPT-OSS 120B — Medium.

## Goal
Verify the supplied Python/FastAPI/OmniRoute foundation independently of frontend integration.

## Read only
- `AGENTS.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/ARCHITECTURE.md`
- `backend/.env.example`
- `backend/requirements.txt`
- `backend/app/config.py`
- `backend/app/main.py`
- `backend/app/routers/health.py`
- `backend/app/routers/chat.py`
- `backend/app/services/llm.py`
- backend tests only as needed

## Execute
1. Create/use `backend/.venv`; install `backend/requirements.txt`.
2. Create `backend/.env` from example if absent. Never print/commit its real secret.
3. Run backend tests that do not require the real OmniRoute key.
4. Start FastAPI and verify `GET /health`.
5. If `OMNIROUTE_API_KEY` is still blank, finish all non-secret work, tell the user to insert it locally in `backend/.env`, update status as `AG3 waiting for local key`, and STOP. Do not ask them to paste it into chat.
6. If the key is present, verify `POST /api/chat` with the normal configured route.
7. Verify one direct Gemini route (`gemini/gemini-3.1-flash-lite`) and one direct Pollinations route (`pol/qwen-coder`) through the backend API. Keep test prompts tiny.
8. Confirm streaming body returns real text and no model response is canned.
9. Fix only backend foundation compatibility/runtime issues.
10. Update status; commit/push successful AG3 changes.

## Runtime token discipline
Each route test should use a tiny prompt such as “Reply exactly: ROUTE OK”. Do not run repeated long generations.

## Do not
- integrate browser/frontend streaming yet (AG4)
- create the final research DB schema
- implement scope guard/attacks/defenses
- change normal routing from `auto/best-coding` unless there is a demonstrated compatibility reason

## Finish
STOP after backend route verification. Report concise completed/changed/tests/blocker/commit. Do not continue to AG4.
