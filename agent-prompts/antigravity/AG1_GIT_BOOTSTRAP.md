# AG1 — Git/GitHub + Secret-Safe Bootstrap

**Select before starting:** GPT-OSS 120B — Medium.

## Goal
Establish a safe local/private Git baseline without spending quota on application work.

## Read only
- `AGENTS.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `.gitignore`
- `backend/.env.example`
- `frontend/.env.local.example`

Do not scan application source unless a Git command specifically requires it.

## Execute
1. Confirm the folder contains the supplied starter; do not regenerate it.
2. Verify `.gitignore` protects `.env`, API keys, runtime DBs, virtualenvs, `node_modules` and `.next`.
3. Initialize Git if needed; branch must be `main`.
4. Inspect `git status` and ensure no secret/runtime artifact is staged.
5. Make one initial commit of the supplied starter.
6. Run `gh auth status`.
7. If authenticated and no remote exists, create a **private** GitHub repo named `PromptGuard-Ai`, add `origin`, push `main`.
8. If an origin already exists, do not recreate it; verify it is the intended repo and push if safe.
9. If GitHub CLI is not authenticated/available, do not invent credentials. Record the one exact blocker in status and stop after local Git is safe.
10. Update `docs/IMPLEMENTATION_STATUS.md` with AG1 result, model used and commit hash.

## Do not
- install npm/pip dependencies
- create `.env` with a real key
- modify frontend/backend application code
- implement any app/research feature
- create CI/CD, branches or workflows

## Verification
- `git status` is clean after commit, or only expected ignored/local files remain
- `git branch --show-current` = `main`
- secret paths are not tracked
- `git remote -v` is correct if GitHub was configured

## Finish
If successful, commit/push AG1 state as needed and STOP.

Return no more than:
- Completed
- Files changed
- Git/GitHub status
- Tests/checks run
- Blocker (if any)
- Commit hash

Do not continue to AG2.
