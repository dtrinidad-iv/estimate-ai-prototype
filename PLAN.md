# EstimateAI — Prototype Build Plan

Goal: upload a roof measurement PDF → extract & verify measurements → generate a basic material + labor estimate.
Stack: Python (FastAPI) · React (Vite + TypeScript) · SQLite for dev, PostgreSQL/Supabase-ready via `DATABASE_URL` · Claude API for AI-assisted extraction only (never for math).

Status legend: `pending` · `wip` · `done` · `blocked`
Update with `python3 scripts/plan.py <status> <task#>`; add with `python3 scripts/plan.py add "<phase>" "<task>" "<description>"`.

## Phase 1: Prototype

| #  | Task | Description | Status |
|----|------|-------------|--------|
| 1  | Requirements analysis | Define prototype scope, data flow, and the deliberate "AI never does the math" rule | done |
| 2  | Project scaffold | `backend/` (FastAPI, venv, requirements) and `frontend/` (Vite React TS) folders, dev scripts | done |
| 3  | Database schema | Tables: jobs, measurement reports, measurements (value + source + confidence), materials, labor rates, assemblies, estimates, line items; seed price data | done |
| 4  | Sample measurement PDFs | Generator for 2 fictional provider formats (different layouts/labels) so the demo runs without real customer reports | done |
| 5  | PDF text extraction | `pdfplumber` text/table extraction + provider auto-detection by fingerprint keywords | done |
| 6  | Provider parsers | One template parser per provider (regex/label maps) → normalized measurement schema; easy to add new providers | done |
| 7  | AI fallback extraction | For unknown layouts: Claude reads the PDF and returns structured JSON (Pydantic schema). Values flagged "AI — needs review". Disabled gracefully without an API key | done |
| 8  | Measurement verification | Deterministic checks: pitch-breakdown sum = total area, facets/area sanity, lengths ≥ 0, eave+rake ≈ perimeter, missing fields; per-field confidence + warnings | done |
| 9  | Material quantity calculator | Configurable formulas (JSON) per material: coverage, waste %, rounding to bundles/rolls/pieces, using `Decimal` | done |
| 10 | Pricing & estimate engine | Material prices, labor rates (per square, pitch/steep adders), assemblies, cost → margin → recommended selling price | done |
| 11 | REST API | Upload, get/patch measurements, verify, generate estimate, edit line items, list price book | done |
| 12 | UI — Upload | Drag-and-drop PDF upload, provider detected, sample PDF download links | done |
| 13 | UI — Review & correct | Editable measurement table with source/confidence badges and validation warnings | done |
| 14 | UI — Estimate editor | Line items with editable qty/price, margin control, totals, cost vs. sell summary | done |
| 15 | Tests | Unit tests for parsers, verification rules, and calculator math | done |
| 16 | Docs & demo | README (setup, architecture, how to add a provider), demo walkthrough, write-up of the extraction/verification design | done |

## Phase 2: Dev workflow

| #  | Task | Description | Status |
|----|------|-------------|--------|
| 17 | CLAUDE.md | Project guide for Claude Code: commands, architecture, rules, definition of done | done |
| 18 | Hooks | Test/type-check after edits, full check before finishing, plan summary at session start | wip |
| 19 | Agents | test-runner, code-reviewer, provider-parser-builder subagents | done |
| 20 | Plan tracking | `scripts/plan.py` to list/update/add tasks in PLAN.md | done |

## Phase 3: Backlog

| #  | Task | Description | Status |
|----|------|-------------|--------|
| 21 | Git repository | Initialize git, first commit, optional CI running the same checks as the hooks | done |
| 22 | CRM integration | Push approved estimates / pull contacts and jobs through the contractor's CRM API | pending |
| 23 | Production handoff | AI reviews the approved estimate, flags missing or conflicting details, creates correction tasks; production manager approves | pending |
| 24 | Real provider templates | Add a template parser per real measurement provider from client sample reports | pending |
| 25 | Customer proposal PDF | Branded proposal with good/better/best options from assemblies | pending |
| 26 | Multi-company SaaS | Per-company price books, branding, users and auth | pending |
| 27 | Portfolio polish | Repo topics, README screenshots | done |
