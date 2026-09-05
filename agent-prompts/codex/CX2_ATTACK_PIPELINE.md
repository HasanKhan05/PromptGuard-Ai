# CX2 — Attack Eligibility + Selected Attack Generation

**Select before starting:** GPT-5.6 Terra — High.

## Goal
Implement the adversarial transformation workflow with minimum runtime calls/tokens.

## Read only
- `AGENTS.md`
- `docs/RESEARCH_RULES.md`
- `docs/TOKEN_RULES.md`
- existing chat/LLM/config schemas/services
- frontend eligibility/experiment components only if needed for API contract consistency

## Implement
Endpoints:
- `POST /api/attacks/eligibility`
- `POST /api/attacks/generate`

Eligibility:
- one LLM call evaluates **all four families together**
- compact structured JSON
- statuses: high / medium / not_applicable (or equivalent stable enum)
- short reason per family
- no four-call fanout

Attack generation:
- one call only after user selects a family
- preserve original developer task context
- output one editable attack prompt, not a long explanation
- support original prompt + family input contract suitable for regenerate/restore in frontend

Family applicability:
- direct injection: broadly applicable
- canary leakage: often applicable using fake protected canary context
- tool misuse: meaningful only when project/issue/file-reading tool context exists
- untrusted code/text: meaningful when code/config/log/docs/text is supplied

Add focused tests for schemas and obvious applicability contracts. Mock external LLM in tests; do not spend live tokens for unit tests.

Update status; commit/push CX2.

## Do not
- add RAG/retrieval
- generate all four attacks automatically
- implement paired experiments yet
- add evaluator chains

## Finish
STOP after CX2. Do not continue to CX3.
