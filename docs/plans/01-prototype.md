# 01 — Prototype: PDF → verified measurements → estimate

**Status:** Done
**Commits:** `20f77fd` (initial commit)

## Goal
A working prototype a roofing contractor can try: upload a roof measurement PDF, extract and verify the measurements, and get a basic material and labor estimate with a recommended selling price. It must stay generic (no client branding) so it can be shown to several prospects.

Out of scope: CRM integration, production handoff, multi-company accounts, customer-facing proposal PDF.

## Decisions
- **Stack:** FastAPI + SQLAlchemy 2.0 (SQLite locally, Postgres/Supabase through `DATABASE_URL`), React + Vite + TypeScript with plain CSS and no UI library.
- **AI reads, code calculates.** Template parsers handle known layouts. A generic label parser handles unknown ones, and Claude (`claude-opus-5-5`, structured outputs, server-side refusal fallback) only fills fields still missing in unknown layouts. Unit conversion, checks, quantities and pricing are all deterministic `Decimal` code.
- **Provenance per value:** source, confidence, PDF evidence, original value and a confirmed flag. Edits become `manual`.
- **Formulas are data:** `pricebook.json` expressions run through a safe AST evaluator (`formula.py`). `eval` is never used.
- **Fictional sample providers** (SkyMeasure Pro, AeroRoof Analytics), so the demo copies nobody's format or branding.
- **Port 8010.** Port 8000 belongs to another local project.

## Backend (`backend/`)
- `app/models.py`: Job, Report, Measurement, Material, LaborRate, Assembly, Estimate, LineItem.
- `app/fields.py`: canonical measurement fields (area, pitch, facets, ridge/hip/valley/rake/eave, flashing, perimeter, squares, waste).
- `app/extraction/`: `text.py` (pdfplumber), `providers/` (SkyMeasure, AeroRoof and generic parsers, plus a registry), `ai.py` (Claude fallback that checks every number against the PDF text), `pipeline.py`.
- `app/verification.py`: errors (missing required field, pitch areas more than 5% off, pitch out of range, zero eaves) block estimating. Warnings: squares and perimeter mismatches, low slope, implausible geometry, unconfirmed generic or AI values.
- `app/calculator.py`: `ceil(basis × (1+waste) / coverage)`, default waste from the report or roof complexity, steep-charge bands taken from the area-by-pitch table.
- `app/services.py`: create report, update measurements, generate estimate from an assembly, recalc that keeps overrides, totals. `price = cost / (1 − margin)`, rounded up to the next $10.
- `app/main.py`: REST API under `/api` (reports, samples, measurements PATCH, estimates, line items, price book). Serves `frontend/dist`.
- `app/config/pricebook.json`: 14 materials, 9 labor and other rates, 2 assemblies (Architectural, Economy 3-tab).
- `scripts/make_samples.py`: 4 demo PDFs (clean, different layout, deliberately broken, unknown format).

## Frontend (`frontend/`)
- `src/api.ts`: types matching `schemas.py`, plus a fetch client.
- Pages:
  - Home: upload, samples, recent jobs.
  - Review: measurement table with source badges and evidence, the check panel, area-by-pitch editor, PDF side by side, assembly picker.
  - Estimate: waste, margin and tax controls; editable quantities and prices; per-line formula view; reset; summary; print.
  - Price book: editable prices.

## Tests
31 tests:
- `test_parsers.py`: both templates, a missing value isn't guessed, the generic parser.
- `test_verification.py`: every rule.
- `test_calculator.py`: evaluator safety, rounding, waste, steep bands, margin math.
- `test_ai.py`: fake client; fills only missing fields; numbers not found in the PDF are flagged; squares converted in code; templates never call AI.
- `test_api.py`: upload → blocked → fix → estimate → override → waste change → reset.

## Verification
pytest, `tsc -b` and `npm run build` pass. Each page was checked in headless Chrome screenshots at desktop and 500px width. The AI path is tested only with the fake client; no live API key was available.

## Follow-ups
- Live test of AI extraction with a real `ANTHROPIC_API_KEY`.
- Alembic migrations before the schema changes again.
