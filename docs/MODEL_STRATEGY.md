# Agent Model Strategy — Usage-Efficient Development

## Goal
Maximize the amount of useful development possible under agent limits **without lowering project correctness**. Use expensive/strong models only where their reasoning materially reduces risk.

## Antigravity pools
The user's current Antigravity picker shows:
- Gemini 3.8 Flash — High
- Gemini 3.7 Flash — Medium
- Gemini 3.6 Flash — Medium
- Gemini 3.1 Pro — Low
- Claude Sonnet 4.6 — Thinking
- Claude Opus 4.6 — Thinking
- GPT-OSS 120B — Medium

The UI shows a Gemini allowance pool and a shared Claude/GPT pool. The phase plan intentionally consumes both instead of exhausting one early.

Default allocation:
- GPT-OSS: routine repo/backend plumbing
- Gemini 3.6/3.7: mechanical-to-normal implementation
- Gemini 3.8 High: one complex streaming integration phase
- Claude Sonnet Thinking: one independent foundation audit / difficult debugging
- Claude Opus: emergency only

There is no claim that one displayed reasoning level has a precise fixed multiplier. Actual usage depends on task size and agent work. The plan controls what we can control: task scope, context, model strength and number of iterations.

## Codex models
As of 2026-09-05, official OpenAI documentation states that eligible paid users can select GPT-5.6 Sol, Terra and Luna in Codex. Luna is the fastest/lowest-cost tier, Terra is balanced, and Sol is the flagship tier.

For this project:
- **Luna Medium**: inspection, aggregation, mechanical verification
- **Terra Medium**: normal implementation/integration
- **Terra High**: security/prompt/evaluator logic that needs more reasoning
- **Sol High**: paired-experiment engine and final scientific audit only
- **Max/Pro/Astra**: not part of the default plan; use only after ChatGPT reviews a persistent blocker

Official references used to plan the Codex model allocation:
- https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt/
- https://help.openai.com/en/articles/11369540
- https://help.openai.com/en/articles/11481834-chatgpt-rate-card

## Context-efficiency rules for both agents
1. The user's launcher is one line; detailed instructions live in the repository.
2. Phase files list exact docs/folders to inspect.
3. No phase may continue automatically.
4. Do not paste prior agent transcripts into the next agent; persist durable state in `docs/IMPLEMENTATION_STATUS.md` and Git.
5. If stuck, provide the error and relevant files only. Do not request a whole-repo rewrite.
6. Prefer a focused stronger-model rescue over repeatedly asking a weaker model the same failing task.
