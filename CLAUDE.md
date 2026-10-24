# EstimateAI

Roofing estimating app: upload a roof measurement PDF → extract and verify measurements → material & labor estimate with a recommended selling price. FastAPI + SQLAlchemy back end (`backend/`), React + Vite + TypeScript front end (`frontend/`). Architecture and rationale: `docs/DESIGN.md`. Setup and demo script: `README.md`.

## Commands

| What | Command |
|------|---------|
| Backend tests | `cd backend && .venv/bin/python -m pytest -q` |
| Frontend type-check | `cd frontend && npx tsc -b` |
| Frontend build | `cd frontend && npm run build` |
| Dev servers (API :8010 + Vite :5173) | `./dev.sh` |
| Single-process demo | build frontend, then `cd backend && .venv/bin/uvicorn app.main:app --port 8010` |
| Regenerate sample PDFs | `cd backend && .venv/bin/python -m scripts.make_samples` |
| Open tasks / update status | `python3 scripts/plan.py` · `python3 scripts/plan.py wip 22` · `python3 scripts/plan.py done 22` |
| Add a task | `python3 scripts/plan.py add "Backlog" "Task name" "Description"` |

The API runs on **port 8010**. Port 8000 belongs to another local project; don't use or kill it.

## Plan tracking (required)

`PLAN.md` is the source of truth for what's being built, organized as phase tables with `pending · wip · done · blocked` status.

- Before starting work, find the matching task, or add one with `scripts/plan.py add`. Mark it `wip`.
- Mark a task `done` only after its checks pass: backend tests, `tsc -b`, and `npm run build` for UI changes.
- Split anything bigger than about a day into separate tasks. Don't leave tasks `wip` at the end of a session unless they really are unfinished, and then say what's left.

## Definition of done

1. Tests cover the change: parser → `tests/test_parsers.py`, checks → `test_verification.py`, math → `test_calculator.py` with a hand-computed expected value in a comment, endpoints → `test_api.py`, AI code → `test_ai.py` with the fake client (never the network).
2. `pytest`, `tsc -b` and `npm run build` pass.
3. Pydantic schemas in `backend/app/schemas.py` and TS types in `frontend/src/api.ts` match.
4. README/DESIGN updated if behavior a user or developer sees changed.
5. PLAN.md updated.

Hooks in `.claude/settings.json` enforce part of this. After each Write/Edit, Python changes run pytest and TS changes run tsc. Before Claude stops, the full check runs if code changed. Edits made through Bash are only caught by the stop check.

## Rules that matter

- **AI reads, code calculates.** Claude (`app/extraction/ai.py`) only reads values from documents the template and generic parsers can't handle. It never computes quantities, prices, unit conversions or totals. AI values are stored with `source="ai"`, a verbatim quote, and confidence lowered when the number isn't in the PDF text. Reviewers must confirm them.
- **Decimal everywhere** in backend money and quantity math. Convert to float only when serializing in `main.py`. Material quantities round up (`ROUND_CEILING`) to purchasable units; money rounds half-up to cents. Margin is on selling price: `price = cost / (1 - margin)`.
- **Formulas are data.** Material and labor quantities come from expressions in `app/config/pricebook.json` (seeded into the DB), evaluated by the safe AST evaluator in `app/formula.py`. Never use `eval`.
- **Provenance.** Every measurement keeps `source`, `confidence`, `evidence` and `original_value`. Edits become `source="manual"`. Estimator line-item overrides set `overridden` and survive recalculation.
- **Verification gates estimates.** `verification.py` errors block `generate_estimate`; warnings don't.
- **Generic branding.** This is a portfolio prototype shown to multiple clients. Don't put real client, company or measurement-provider names or branding in code, samples or UI. Sample providers (SkyMeasure Pro, AeroRoof Analytics) are fictional.
- **Claude API defaults:** model `claude-opus-5-5` (env `EXTRACTION_MODEL`), structured outputs via `client.beta.messages.parse` with the server-side fallback beta. Without `ANTHROPIC_API_KEY` the app must still work.

## Where things live

```
backend/app/extraction/providers/   one template parser per report layout (+ generic.py); register in __init__.py
backend/app/extraction/pipeline.py  template → generic → AI (missing fields only)
backend/app/fields.py               canonical measurement fields
backend/app/verification.py         deterministic checks
backend/app/calculator.py           quantities, waste, steep-pitch bands
backend/app/services.py             reports, estimates, totals
backend/app/main.py                 REST API under /api, serves frontend/dist
frontend/src/pages/                 Home (upload), Review, Estimate, PriceBook
```

The SQLite DB (`backend/data/estimateai.db`) is created on startup. Deleting it resets data, and the price book reseeds from JSON. Schema changes need the DB deleted until migrations (Alembic) are added.

## Agents (`.claude/agents/`)

- **test-runner:** runs the full check suite and diagnoses failures. Use before marking a task done.
- **code-reviewer:** reviews changes against the rules above. Use before finishing a feature or committing.
- **provider-parser-builder:** adds a template parser + tests for a new measurement-report layout from a sample PDF.

## Style

Match the surrounding code. Python is typed, with small functions and sparse comments that explain *why*. React uses function components and the plain CSS tokens in `index.css`, with no UI library. Keep the API under `/api`.
