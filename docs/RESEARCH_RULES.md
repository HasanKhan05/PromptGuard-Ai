# Research Rules — Compact Codex Reference

## Research question
How effective are lightweight application-level guardrails at reducing LLM attacks while preserving the usefulness of a software-development assistant?

## Assistant domain
Normal software-development assistant: programming Q&A, debugging, code review/explanation, software architecture, development tools and software-engineering concepts.

The scope/domain guard is ordinary app behavior, not one of the four research defenses.

## Exactly four attack → defense pairs
1. Direct Prompt Injection → Input Screening
2. System Prompt / Canary Leakage → Output Screening
3. Tool Misuse / Manipulation → Tool Authorization / Least Privilege
4. Untrusted Code/Text Injection → Instruction–Data Separation

## No RAG overlap
Do not add RAG poisoning, poisoned documents, vector DB attacks, retrieval experiments, source trust reranking, BM25/dense comparisons, FAISS or sentence-transformers.

## Harmless tools only
Use 2–3 local read-only tools, e.g.:
- `get_project_info(project_id)`
- `read_issue(issue_id)`
- `get_file_summary(file_id)`

No shell execution, file deletion, network side effects or destructive tools.

## Fake canary only
Use a fake value such as `DEV_CANARY_8241`. Never put a real secret in the experiment.

## Paired-test invariant
For one final edited attack prompt:
- exact same prompt
- exact same model/version
- exact same temperature/token limit
- exact same trusted role/system setup except the mapped defense wrapper/state
- exact same tool schema where applicable
- only mapped defense changes

No OmniRoute `auto/...` for paired experiments. Default fixed model: `gemini/gemini-3.1-flash-lite` unless intentionally changed later.

## Configurations
1. Baseline/no research defense
2. Input Screening only
3. Output Screening only
4. Tool Authorization only
5. Instruction/Data Separation only
6. All four layered

## Target cases
Approximately 45–50 attack cases and 35–40 benign cases (~90 total). Do not generate all cases automatically during development unless the user requests the actual benchmark run.

## Core metrics
- Attack Success Rate overall/by family
- Benign task success
- False-refusal rate
- Canary leakage rate
- Unauthorized tool attempts/executions
- Latency
- Input/output tokens
- Cost when reported

## Evaluation principle
Deterministic first. LLM judge only when outcome cannot be reliably derived from explicit evidence. Never invent or infer a final result that the logs do not support.
