# Token Efficiency Rules

PromptGuard must be efficient in **development-agent usage** and **runtime LLM usage**.

# A. Development-agent efficiency
1. One phase per prompt; agent stops at phase boundary.
2. Detailed instructions live in repository files; user launchers stay one line.
3. Read `AGENTS.md`, status and only phase-relevant files.
4. Do not repeatedly summarize the project or inspect unrelated folders.
5. No style-only refactors or architecture rewrites.
6. Targeted tests during implementation; full test/build only at named verification phases.
7. One commit per successful phase.
8. Final phase response should be short: completed, changed files, tests, blocker, commit.
9. If a weaker model is stuck, escalate once with a **focused blocker prompt** rather than spending many retries.

# B. Runtime PromptGuard LLM efficiency

## Expected complete research flow
- normal assistant: 1 call
- eligibility for all four families: 1 compact call
- selected attack generation: 1 call
- baseline: 1 call
- defended: 1 call
- evaluator: 0 or 1 compact call only when deterministic evaluation cannot decide

Typical full path: ~5 calls, occasionally 6 — not multi-agent chains.

## No LLM call for deterministic work
- canary string detection
- tool authorization
- benchmark percentages
- SQLite aggregation
- latency/token/cost arithmetic
- schema validation
- obvious attack success signals that can be measured directly

## Context discipline
- Normal chat: current prompt plus short trusted system role; do not automatically send full conversation history.
- Eligibility: current prompt + compact definitions of all four attack families in one call.
- Attack generation: current task + selected attack family only.
- Experiment: final edited attack prompt + compact controlled system instructions.
- Evaluator: only the minimal evidence required for that case.
- Research summary: compact aggregate metrics, not raw transcripts.

## Output caps — initial targets
Keep configurable, but start roughly at:
- normal developer answer: 1200 output tokens max
- eligibility: 260
- attack generation: 500
- evaluator: 220
- research interpretation: 500

Do not blindly raise limits because a single test response was truncated; inspect whether the prompt/output can be made more compact first.

## Routing
Ordinary assistant/internal support jobs may use OmniRoute auto routing.
Controlled paired experiments must pin the exact configured experiment model.
