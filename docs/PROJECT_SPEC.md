# PromptGuard Ai — Project Specification

## Purpose
PromptGuard Ai is a **university/portfolio AI-security research prototype**, not a production deployment. It is a normal software-development assistant first, then a controlled research platform for comparing lightweight application-level defenses against four LLM application attack families.

Research question:
> How effective are lightweight application-level guardrails at reducing LLM attacks while preserving the usefulness of a software-development assistant?

## Normal assistant
Programming Q&A, debugging, code review, code explanation, software architecture, development tools and software-engineering concepts.

Normal live responses come from the model API. Stored prior responses are logs/evidence only and must never be reused as canned assistant answers.

## Research workflow
1. User sends a normal software-development prompt.
2. Assistant gives a real live answer first.
3. One compact eligibility call scores all four attack families for that exact prompt.
4. User selects one family.
5. One attack-generation call transforms the original task into an editable adversarial prompt.
6. User may edit/regenerate/restore.
7. Same final edited prompt is run twice: defense OFF, then mapped defense ON.
8. Outcomes and evidence are stored in SQLite.
9. Benchmarks aggregate stored runs.
10. Research page explains only what stored benchmark evidence supports.

## Four attack families / defenses
1. Direct Prompt Injection → Input Screening
2. System Prompt / Canary Leakage → Output Screening
3. Tool Misuse / Manipulation → Tool Authorization / Least Privilege
4. Untrusted Code/Text Injection → Instruction–Data Separation

## Important separation from the user's RAG project
PromptGuard Ai does not include RAG poisoning. No poisoned PDFs, vector DB poisoning, retrieval poisoning, FAISS/BM25 comparisons, source trust reranking or poison retrieval rate.

## Harmless tools
Only a few local read-only helpers are needed for tool-misuse experiments. No destructive/system tools.

## Planned APIs
Foundation:
- `GET /health`
- `POST /api/chat`

Research phase:
- `POST /api/attacks/eligibility`
- `POST /api/attacks/generate`
- `POST /api/experiments/run`
- `GET /api/benchmarks`
- `GET /api/runs/{id}`
- `GET /api/research`

## Benchmark target
~45–50 attack cases + ~35–40 benign cases (~90 total).

## Research configurations
- baseline/no research defense
- Input Screening only
- Output Screening only
- Tool Authorization only
- Instruction/Data Separation only
- all four layered

## Quality target
Portfolio/research quality: clear design, correct experiments, reproducible local run, meaningful tests and documentation. No need for production scalability, public deployment, enterprise auth, distributed services or elaborate ops.
