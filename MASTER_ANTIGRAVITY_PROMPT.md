# Antigravity Master Contract — DO NOT EXECUTE ALL PHASES AT ONCE

This file is a contract/index, not a single giant implementation prompt.

PromptGuard Ai is a university/portfolio research prototype. The user is deliberately switching Antigravity models between phases to balance the Gemini and Claude/GPT allowance pools. Therefore:

1. Read `AGENTS.md`.
2. Read only the **specific AG phase file** named in the user's current prompt.
3. Execute that phase only.
4. Update `docs/IMPLEMENTATION_STATUS.md`.
5. Make the phase commit/push if the phase asks for it.
6. STOP. Never continue to the next AG phase without a new user message.

Phase files:
- `agent-prompts/antigravity/AG1_GIT_BOOTSTRAP.md`
- `agent-prompts/antigravity/AG2_FRONTEND_VERIFY.md`
- `agent-prompts/antigravity/AG3_BACKEND_OMNIROUTE.md`
- `agent-prompts/antigravity/AG4_STREAMING_INTEGRATION.md`
- `agent-prompts/antigravity/AG5_SQLITE_TESTS.md`
- `agent-prompts/antigravity/AG6_FOUNDATION_AUDIT.md`

Hard stop after AG6. Do not implement Codex CX0-CX8 research/security phases.
