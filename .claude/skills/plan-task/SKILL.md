---
name: plan-task
description: Write a task plan in docs/plans/NN-task-name.md with Status Proposed, add it to the index, and stop for approval. Use before building anything that touches more than 3 files, or whenever the user asks for a plan.
argument-hint: "[task description]"
---

# Plan a task

Task: $ARGUMENTS

## Steps
1. **Read first.** Read CLAUDE.md, `docs/plans/README.md`, and the most recent plans related to this task. Open the real code you'll build on; don't plan against code you haven't read.
2. **Ask only about real forks**, where the user's answer changes the plan. For anything with an obvious default, choose it and say so in the plan.
3. **Number and name.** The next `NN` is the highest in `docs/plans/` + 1, zero-padded. Name the file after the task in kebab-case, e.g. `06-crm-integration.md`.
4. **Write the plan** using the template below. Be specific: name the actual files, endpoints, fields, formulas and tests.
5. **Add a row** to the table in `docs/plans/README.md`: `| NN | [Title](NN-task-name.md) | Proposed |`.
6. **Stop.** Summarize the plan in a few lines and ask for approval. Build nothing until the user says go. On approval, change Status to **WIP** in both the plan and the index.

If the task was planned in plan mode instead, skip steps 4–6's "stop": write the approved plan into the template with Status **WIP**, add the index row as WIP, then build.

## Template
```markdown
# NN — Title

**Status:** Proposed

## Goal
What this adds and why, in 2-3 sentences. What is explicitly out of scope.

## Decisions
Choices made, with one line on why each. Note any new dependency and why it's needed (needs the user's OK).

## Backend (`backend/`)
Models (and whether the DB must be recreated — no migrations yet), fields in `fields.py`, parsers, verification rules, calculator/pricing changes, price-book JSON, services, schemas, endpoints.

## Frontend (`frontend/`)
Types in `src/api.ts`, pages, components, CSS.

## Tests
Which test files get which cases. Every money/quantity expectation is hand-computed in a comment (e.g. `2,200 × 1.10 ÷ 33.333 = 72.6 → 73`). AI code is tested with the fake client only.

## README screenshots
New or retaken shots in `docs/screenshots/` (file name and what each shows), or "none" and why. Captured as in plan 04.

## Verification
pytest, `tsc -b`, `npm run build`; `test-runner` and `code-reviewer` agents on the diff; manual flow in the browser if UI changed.

## Commits after approval
`feat(backend): ...`, `feat(frontend): ...`, then this plan → Done.
```

## Rules
- AI never computes quantities, prices, conversions or totals; it only reads documents (CLAUDE.md "AI reads, code calculates").
- Money and quantities stay `Decimal` in the backend.
- No real client, company or measurement-provider names or branding.
- New env keys go in the README's setup section with a comment. Never commit `.env`.
