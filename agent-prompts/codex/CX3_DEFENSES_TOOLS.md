# CX3 — Four Defenses + Harmless Read-Only Tools

**Select before starting:** GPT-5.6 Terra — High.

## Goal
Implement exactly the four research defenses with simple deterministic application logic where possible.

## Read only
- `AGENTS.md`
- `docs/RESEARCH_RULES.md`
- `docs/TOKEN_RULES.md`
- CX2 attack contracts
- backend guard/tool/service files relevant to this phase

## Implement exactly
1. Direct Prompt Injection → **Input Screening**
   - lightweight screening; intentionally not “block everything”
   - allow suspicious-but-legitimate code review cases where possible

2. Canary/System Leakage → **Output Screening**
   - fake canary e.g. `DEV_CANARY_8241`
   - deterministic canary detection/redaction/prevention
   - later logs must distinguish raw-model leakage vs user-visible application leakage prevention

3. Tool Misuse → **Tool Authorization / Least Privilege**
   - 2–3 harmless local read-only tools only
   - suggested: `get_project_info`, `read_issue`, `get_file_summary`
   - deterministic allow/deny based on resource/params/scope
   - model proposes; Python authorization decides; no destructive action

4. Untrusted Code/Text Injection → **Instruction–Data Separation**
   - submitted code/text is wrapped/marked as untrusted data
   - embedded instructions must not become trusted commands
   - no RAG

Keep interfaces small so CX4 can toggle each mapped defense cleanly. Add targeted deterministic tests. No live model calls needed for canary/tool authorization tests.

Update status; commit/push CX3.

## Finish
STOP after CX3. Do not continue to CX4.
