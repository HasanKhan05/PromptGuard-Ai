# PromptGuard Ai — Repository Agent Rules

These rules apply to **Antigravity, Codex, and any other coding agent** that works in this repository.

## 1. Project level
PromptGuard Ai is a **university/portfolio AI-security research prototype**, not a production SaaS deployment.

Build it to be:
- correct enough for a serious undergraduate research/portfolio project
- easy to run locally
- readable and reproducible
- visually polished
- scientifically fair for the paired experiments

Do **not** build enterprise infrastructure or spend agent/runtime tokens on production-only concerns.

## 2. Frozen stack
Frontend:
- Next.js App Router
- React
- TypeScript
- Tailwind CSS / existing CSS
- Lucide Icons
- React Markdown
- native `fetch` streaming

Backend:
- Python
- FastAPI
- Pydantic
- SQLite
- SQLAlchemy
- OpenAI-compatible client pointed at OmniRoute
- pytest
- pandas only when benchmark aggregation actually needs it

LLM gateway:
- local OmniRoute: `http://localhost:20128/v1`

Do not add a framework merely because it is popular.

## 3. Do NOT add unless the user explicitly changes scope
No LangChain, LangGraph, Redis, Celery, PostgreSQL, Supabase, vector database, Docker orchestration, Kubernetes, microservices, message queues, complex auth, production observability stack, cloud deployment architecture, paid infrastructure, or elaborate CI/CD.

## 4. Development-agent usage must stay low
- Execute **one phase only** per user prompt.
- Read only the files listed by the current phase plus files directly required by an error.
- Do not rescan/summarize the whole repo every turn.
- Do not refactor working code for aesthetics.
- Do not rewrite supplied frontend code from scratch.
- Prefer targeted tests while working; full verification only at phase boundaries that request it.
- Keep plans internal/short when requirements are already explicit.
- Keep completion reports concise: completed, changed files, tests, blocker, commit.
- Do not browse the web unless an actual dependency/runtime problem requires current documentation.
- Make at most one sensible commit per completed phase unless a blocker requires a checkpoint commit.

## 5. Runtime LLM/API usage must stay low
PromptGuard must remain functional without becoming token-heavy.
- One LLM call when one call is sufficient.
- Never use an LLM for deterministic checks Python can do.
- Do not resend full chat history unless a feature genuinely needs it.
- Eligibility evaluates all four attack families in one compact structured call.
- Generate only the attack family selected by the user.
- Paired experiment: exactly one baseline call + one defended call; optional evaluator only when deterministic evaluation is insufficient.
- Canary detection, tool authorization, benchmark arithmetic, database aggregation and obvious validations are deterministic.
- Internal responses should be compact structured JSON.
- Stored outputs are research evidence only; never reuse them as canned live assistant answers.

See `docs/TOKEN_RULES.md`.

## 6. Research integrity — hard rules
Four attack families only:
1. Direct Prompt Injection → Input Screening
2. System Prompt / Canary Leakage → Output Screening
3. Tool Misuse / Manipulation → Tool Authorization / Least Privilege
4. Untrusted Code/Text Injection → Instruction–Data Separation

PromptGuard Ai must **not repeat the separate RAG-poisoning project**. No poisoned PDFs, vector DB poisoning, retrieval poisoning, BM25-vs-dense experiments, source trust reranking, or poison retrieval rate.

For paired experiments, keep the final edited attack prompt, exact model, temperature, token limit, trusted role/system configuration and tool schema the same. **Only the mapped defense state changes.** Never use OmniRoute `auto/...` in controlled baseline-vs-defended runs.

Never invent benchmark results. Initial UI numbers are illustrative preview values only.

## 7. Git/secrets
- Private GitHub repository initially.
- Never commit `.env`, API keys, secrets, local DB files, `node_modules`, `.next`, or virtual environments.
- Work on the same local repository/folder across Antigravity and Codex.
- Do not create branches/worktrees unless the user explicitly asks; phase commits on `main` are enough for this project.

## 8. Phase boundary
The user is controlling model selection between phases. **Never continue into the next phase automatically.**

Read the exact phase prompt under:
- `agent-prompts/antigravity/` during the Antigravity foundation stage
- `agent-prompts/codex/` during the Codex research stage

After each phase, update `docs/IMPLEMENTATION_STATUS.md`, commit if instructed, then STOP and report concisely.
