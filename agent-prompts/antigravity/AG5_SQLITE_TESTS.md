# AG5 — Minimal SQLite Persistence + Targeted Tests

**Select before starting:** Gemini 3.6 Flash — Medium.

## Goal
Verify the tiny local persistence layer works. Do not pre-build the research database.

## Read only
- `AGENTS.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `backend/app/db.py`
- `backend/app/models.py`
- `backend/app/routers/chat.py`
- `backend/tests/test_db.py`
- related backend test files only

## Execute
1. Verify SQLite initializes automatically.
2. Verify the supplied minimal `chat_runs` table is created.
3. Verify a completed live/mock-safe chat run can store prompt, response, requested model and actual model.
4. Add/fix only lightweight tests needed to prove initialization/persistence.
5. Do not store partial empty rows when a stream fails before producing content.
6. Ensure runtime DB files remain gitignored.
7. Run targeted backend tests.
8. Update status; commit/push AG5.

## Do not
- design experiment/attack/defense tables
- add migrations/Alembic unless a real need appears later (not expected)
- add Postgres/Supabase
- add repositories/service abstractions merely for style

## Finish
STOP after AG5. Concise report only. Do not continue to AG6.
