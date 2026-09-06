# PromptGuard Ai — Phase Launchers and Model Selection

This is the **user-facing execution sheet**. Select the listed model/effort **before** sending the launcher. After every phase, return the agent's exact reply to ChatGPT before moving on.

The model allocation intentionally spreads work between Antigravity's **Gemini pool** and **Claude/GPT pool**, and between Codex's cheaper/balanced/flagship models. It is a default plan; ChatGPT may change the next model after seeing an error or a usage screenshot.

## Antigravity foundation

| Phase | Task | Default model | Level | Why |
|---|---|---|---|---|
| AG1 | Git/GitHub + secret-safe bootstrap | **GPT-OSS 120B** | **Medium** | Routine repo work; preserves Gemini pool and uses the separate Claude/GPT allowance. |
| AG2 | Frontend install/build + visual sanity | **Gemini 3.7 Flash** | **Medium** | Good balance for TypeScript/UI work without High reasoning. |
| AG3 | Python env + FastAPI + OmniRoute route verification | **GPT-OSS 120B** | **Medium** | Straightforward backend plumbing; again balances the two allowance pools. |
| AG4 | End-to-end streaming integration | **Gemini 3.8 Flash** | **High** | Most integration-sensitive Antigravity task; worth the stronger model. |
| AG5 | Minimal SQLite persistence + targeted tests | **Gemini 3.6 Flash** | **Medium** | Mechanical/local work; stronger model would waste quota. |
| AG6 | Independent foundation audit + Git handoff | **Claude Sonnet 4.6** | **Thinking** | One cross-model quality pass using the other pool; fix blockers only, no feature expansion. |

### Exact Antigravity launchers
AG1:
`Read agent-prompts/antigravity/AG1_GIT_BOOTSTRAP.md and execute that phase exactly. Do not continue to AG2.`

AG2:
`Read agent-prompts/antigravity/AG2_FRONTEND_VERIFY.md and execute that phase exactly. Do not continue to AG3.`

AG3:
`Read agent-prompts/antigravity/AG3_BACKEND_OMNIROUTE.md and execute that phase exactly. Do not continue to AG4.`

AG4:
`Read agent-prompts/antigravity/AG4_STREAMING_INTEGRATION.md and execute that phase exactly. Do not continue to AG5.`

AG5:
`Read agent-prompts/antigravity/AG5_SQLITE_TESTS.md and execute that phase exactly. Do not continue to AG6.`

AG6:
`Read agent-prompts/antigravity/AG6_FOUNDATION_AUDIT.md and execute that phase exactly. Stop at the Codex handoff boundary.`

## Antigravity escalation policy
Do **not** jump to Opus because of one failure.
1. Same phase/default model gets one focused fix attempt if the issue is obvious.
2. Complex cross-file/streaming bug: switch to **Claude Sonnet 4.6 (Thinking)** with a narrow blocker-only prompt.
3. **Claude Opus 4.6 (Thinking)** is emergency-only if Sonnet fails on the same genuinely difficult blocker. It must inspect only the relevant files and not perform a broad redesign.
4. **Gemini 3.1 Pro Low** is a quota-conservation fallback for routine Gemini work only if ChatGPT explicitly recommends it.
5. Send ChatGPT the usage screenshot when either allowance pool gets materially lower so the next phase can be rebalanced.

---

## Codex research/security implementation

Current official OpenAI availability for Plus/eligible paid Codex includes GPT-5.6 **Luna, Terra and Sol**. This plan intentionally uses Luna for cheap inspection/mechanical work, Terra for most implementation, and Sol only for research-critical logic/audits.

| Phase | Task | Default model | Effort | Why |
|---|---|---|---|---|
| CX0 | Handoff audit / verify Antigravity foundation | **GPT-5.6 Luna** | **Medium** | Cheap inspection and targeted verification. |
| CX1 | Assistant role + scope guard + compact prompting | **GPT-5.6 Terra** | **Medium** | Normal application logic; balanced model is enough. |
| CX2 | Attack eligibility + selected attack generation | **GPT-5.6 Terra** | **High** | Structured prompt contracts require careful reasoning but not flagship cost. |
| CX3 | Four defenses + harmless read-only tools | **GPT-5.6 Terra** | **High** | Mostly deterministic security logic; Terra High should handle it. |
| CX4 | Paired experiment engine + evidence schema | **GPT-5.6 Sol** | **High** | Scientific control is the most critical implementation in the project. |
| CX5 | Evaluator + metrics correctness | **GPT-5.6 Terra** | **High** | Evaluation logic needs care, while deterministic-first design limits complexity. |
| CX6 | Benchmark aggregation + research endpoint | **GPT-5.6 Luna** | **Medium** | Mostly SQLite/Python aggregation and lightweight formatting. |
| CX7 | Wire real research APIs into frontend + remove mocks from live states | **GPT-5.6 Terra** | **Medium** | Integration/UI work, not frontier reasoning. |
| CX8 | Final scientific/security audit + full validation | **GPT-5.6 Sol** | **High** | Second and final Sol use; validate fairness and evidence, do not redesign. |

### Exact Codex launchers
CX0: *Superseded by Antigravity AG6 audit – see `docs/HYBRID_EXECUTION_PLAN.md`*

CX1:
`Read agent-prompts/codex/CX1_ASSISTANT_CONTROL.md and execute that phase exactly. Do not continue to CX2.`

CX2:
`Read agent-prompts/codex/CX2_ATTACK_PIPELINE.md and execute that phase exactly. Do not continue to CX3.`

CX3:
`Read agent-prompts/codex/CX3_DEFENSES_TOOLS.md and execute that phase exactly. Do not continue to CX4.`

CX4:
`Read agent-prompts/codex/CX4_PAIRED_EXPERIMENT.md and execute that phase exactly. Do not continue to CX5.`

CX5:
`Read agent-prompts/codex/CX5_EVALUATOR_METRICS.md and execute that phase exactly. Do not continue to CX6.`

CX6:
`Read agent-prompts/codex/CX6_BENCHMARK_RESEARCH.md and execute that phase exactly. Do not continue to CX7.`

CX7:
`Read agent-prompts/codex/CX7_FRONTEND_RESEARCH_WIRING.md and execute that phase exactly. Do not continue to CX8.`

CX8:
`Read agent-prompts/codex/CX8_FINAL_AUDIT.md and execute that phase exactly. Stop when the project validation/handoff is complete.`

## Codex escalation policy
- Do not use Max/Pro/Astra for normal phases.
- If Luna fails a routine phase, move to Terra Medium.
- If Terra High encounters a genuinely hard research-integrity bug, use Sol High on that **specific blocker**, not a whole-repo rewrite.
- Use Max only if ChatGPT explicitly recommends it after reviewing a persistent blocker and current usage.
- Keep prompts phase-scoped and let Codex read short local docs rather than pasting the entire project description repeatedly.
