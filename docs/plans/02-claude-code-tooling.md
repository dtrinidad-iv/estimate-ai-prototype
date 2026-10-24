# 02 — Claude Code tooling

**Status:** Done
**Commits:** `20f77fd` (CLAUDE.md, hooks, agents), `867d78e` (settings: hooks enabled)

## Goal
Make continued development smooth and safe: Claude knows the project's rules, checks run automatically, and recurring jobs have dedicated agents.

Out of scope: CI (plan 03).

## Decisions
- **CLAUDE.md** covers commands, rules (AI reads / code calculates, Decimal, formulas as data, provenance, generic branding), file layout, definition of done, and when to use each agent.
- **Hooks** (`.claude/hooks/`):
  - `post_edit_check.sh`: after Write/Edit, a `.py`/price-book change runs pytest `-x` and a `.ts`/`.tsx` change runs `tsc -b`. Exit 2 sends the failure back to Claude.
  - `stop_check.sh`: when code has changed since the last green run, runs the full backend tests and type-check before Claude stops, and blocks once on failure (it respects `stop_hook_active`). It also catches Bash edits.
  - `session_start.sh`: puts the open plans into context.
- **Agents** (`.claude/agents/`): `test-runner` (sonnet, read-only), `code-reviewer` (opus, read-only, checks project rules), `provider-parser-builder` (opus, adds a report layout and its tests).
- **Settings file:** the auto-mode classifier blocked Claude from writing `.claude/settings.json` (self-modification), so the user installs it. Proposed content: SessionStart, PostToolUse `Write|Edit` and Stop hooks, plus deny edits to `.venv/` and `node_modules/`.

## Files
- `CLAUDE.md`
- `.claude/hooks/{post_edit_check,stop_check,session_start}.sh`
- `.claude/agents/{test-runner,code-reviewer,provider-parser-builder}.md`
- `.claude/settings.json` (user installs)
- `.gitignore`: `.claude/.last-green`, `.claude/settings.local.json`

## Verification
- Pipe-tested every script: success paths, plus a temporary failing test and a TS type error, both caught (exit 2 / `decision: block`) and then removed.
- Live in a session started from the project folder: the SessionStart hook loaded the open plans, and writing a deliberately failing test made the PostToolUse hook run pytest and send the failure back. The probe was then removed.
- Hooks only load when Claude Code is started inside `estimate-ai-prototype/`. From the parent folder they're ignored (skills still show up).
