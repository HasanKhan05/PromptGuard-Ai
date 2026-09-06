# Handoff Protocol

## User-controlled loop
After each phase:
1. Agent updates `docs/IMPLEMENTATION_STATUS.md`.
2. Agent makes the requested phase commit if successful.
3. Agent stops and returns a short report.
4. User copies the exact report to ChatGPT.
5. ChatGPT reviews it, checks whether the next default model is still appropriate, and supplies the next launcher/model.
All agents must follow `docs/HYBRID_EXECUTION_PLAN.md` for authoritative phase ownership and model schedule.

Do not let Antigravity/Codex autonomously continue across phase boundaries because the user needs to switch model/effort and manage usage.

## If an agent hits a usage limit mid-phase
- Save current files.
- Run only quick sanity checks possible with remaining time.
- Update status with `completed / in progress / blocker`.
- Make a checkpoint commit if the tree is in a safe state.
- Stop.

The next agent/model should inspect `git status`, last commit and `docs/IMPLEMENTATION_STATUS.md`, then continue the same phase rather than restart the project.

## If a phase fails
Do not immediately restart the whole phase with a stronger model. Send ChatGPT:
- exact error
- phase report
- current model/effort
- optional usage screenshot

ChatGPT will decide whether to keep the same model, switch pools, or use a focused rescue prompt.
