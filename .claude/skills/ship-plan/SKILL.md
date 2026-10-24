---
name: ship-plan
description: Commit and push an approved, finished plan - verify, separate backend/frontend/docs commits, mark the plan Done with commit hashes. Use only when the user approves the result ("all good, commit and push").
disable-model-invocation: true
argument-hint: "[plan number, e.g. 06]"
---

# Ship a plan

Plan: $ARGUMENTS. If no number is given, use the plan marked WIP in `docs/plans/README.md` (if several, ask which).

## Steps
1. **Check scope.** Run `git status --short` and `git diff --stat`. Every changed file should belong to this plan. If something unrelated is there, stop and ask; never sweep it into a commit.
2. **Verify.** Run the checks for the sides that changed:
   - backend: `cd backend && .venv/bin/python -m pytest -q`
   - frontend: `cd frontend && npx tsc -b && npm run build`
   If anything fails, stop and report. Never commit red.
3. **Docs check.** Decide whether each applies, and update it in the same commit as the change it describes:
   - New or changed convention, command, port or rule → `CLAUDE.md`.
   - Setup/run steps, env keys or a user-visible feature → root `README.md`.
   - New page or visible feature, or a shot now out of date → `docs/screenshots/` + README "Screenshots". If missing, stop and take it first.
   - New `.claude/` skill, agent or hook → the tooling sections of `CLAUDE.md`.
   - Follow-ups found but not done → the plan's "Follow-ups" section.
   Report which docs you updated, or "no doc changes needed".
4. **Commit by area**, format `type(scope): summary` with a short paragraph on what and why, ending with the attribution line from the system reminder:
   - `git add backend` → `feat(backend): ...` (or `fix`/`refactor`)
   - `git add frontend` → `feat(frontend): ...`
   - `.claude/` and `CLAUDE.md` → `chore(claude): ...`
   - root README / screenshots → `docs: ...`
   Skip areas with no changes.
5. **Mark the plan Done.** Under the plan's title set:
   ```
   **Status:** Done
   **Commits:** `<hash>` (backend), `<hash>` (frontend)
   ```
   Replace any existing `**Commits:**` line. Update the plan's row in `docs/plans/README.md` to `Done`.
6. **Commit the plan:** `git add docs/plans && git commit -m "docs: mark plan NN done"`.
7. **Push:** `GIT_TERMINAL_PROMPT=0 git push`. If it fails on auth, report it; don't change remotes or credentials.
8. **Report:** commit hashes and messages, CI status if available (`gh run list --limit 1`), and confirm `git status` is clean.

## Never
- Commit `.env`, the SQLite DB, uploads, or `.claude/settings.local.json`.
- Use `--no-verify`, force-push, or amend pushed commits.
