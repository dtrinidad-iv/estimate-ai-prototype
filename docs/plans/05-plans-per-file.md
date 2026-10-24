# 05 — One plan file per task

**Status:** Done
**Commits:** `991181b` (claude), `991181b` (docs)

## Goal
Replace the single `PLAN.md` task table with one detailed file per plan in `docs/plans/`, following the same convention as the user's other projects. A plan approved in plan mode (or written with `/plan-task`) is saved as `docs/plans/NN-task-name.md` and tracked through Proposed → WIP → Done.

Out of scope: moving the backlog to GitHub issues. It stays in the README roadmap until an item gets a plan.

## Decisions
- **Format** copied from the user's existing projects: `# NN — Title`, `**Status:**`, `**Commits:**`, then Goal / Decisions / Backend / Frontend / Tests / README screenshots / Verification. The index lives in `docs/plans/README.md`.
- **Plan mode:** on approval, Claude writes the approved plan to the next `NN` file with Status WIP and adds it to the index before building. The global `plansDirectory` is left alone, so plan mode's scratch files don't pile up in the repo with random names.
- **Skills:** `/plan-task` writes a Proposed plan and stops for approval. `/ship-plan` verifies, commits by area, marks the plan Done with hashes, and pushes. `ship-plan` is user-invoked only.
- **Commit format:** `type(scope): summary` (`feat(backend)`, `feat(frontend)`, `chore(claude)`, `docs`), as in the other projects.
- Backfilled plans 01–04 from this project's history.

## Files
- `docs/plans/README.md` + `01`–`05` plan files (new)
- `.claude/skills/plan-task/SKILL.md`, `.claude/skills/ship-plan/SKILL.md` (new)
- `.claude/hooks/session_start.sh`, `.claude/hooks/stop_check.sh`: read open plans from the index instead of `PLAN.md`
- `.claude/agents/test-runner.md`: wording
- `CLAUDE.md`: workflow section
- `PLAN.md`, `scripts/plan.py` (deleted)

## Verification
Pipe-test both changed hooks; pytest, `tsc -b` and build still green.
