# CX4 — Paired Experiment Engine + Evidence Schema

**Select before starting:** GPT-5.6 Sol — High.

## Goal
Implement the scientifically critical controlled experiment runner. Correctness matters more than feature breadth in this phase.

## Read only
- `AGENTS.md`
- `docs/RESEARCH_RULES.md`
- `docs/ARCHITECTURE.md`
- `docs/TOKEN_RULES.md`
- CX2/CX3 attack/defense interfaces
- current DB model/config/chat LLM service files

## Implement
Endpoint:
- `POST /api/experiments/run`

For one final edited attack prompt, run:
1. baseline: mapped research defense OFF
2. defended: mapped research defense ON

Hard invariant:
- same final edited attack prompt
- same exact fixed model
- same temperature
- same output token cap
- same trusted role/system configuration except the mapped defense mechanism/state required by the comparison
- same tool schema where applicable
- only defense state changes

Never use `auto/...` inside the paired experiment. Use `EXPERIMENT_MODEL`, initially `gemini/gemini-3.1-flash-lite`.

Create the **smallest evidence schema** needed to reproduce/aggregate runs. Capture at least:
- run/experiment id, timestamp
- original prompt
- generated/final edited attack prompt
- attack family
- generation source + edited flag
- exact requested/actual model and parameters
- defense config/version
- relevant system/tool schema version
- baseline and defended responses/evidence
- requested tool/args + auth decision where relevant
- guard results
- latency
- input/output tokens/cost if available
- placeholders/fields for evaluator outcomes populated by CX5

Do not store real secrets. Do not reuse stored outputs as future live answers.

Add tests that prove the runner constructs both calls from the same immutable experiment inputs and toggles only the intended defense. Mock model calls for unit tests.

Update status; commit/push CX4.

## Do not
- run the full ~90-case benchmark now
- use different models between baseline/defended
- add distributed job queues
- add production experiment orchestration

## Finish
STOP after CX4. Do not continue to CX5.
