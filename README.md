# EstimateAI

[![CI](https://github.com/dtrinidad-iv/estimate-ai-prototype/actions/workflows/ci.yml/badge.svg)](https://github.com/dtrinidad-iv/estimate-ai-prototype/actions/workflows/ci.yml)

Upload a roof measurement report → extract and verify the measurements → get a material & labor estimate with a recommended selling price.

A working prototype of an estimating platform for roofing contractors: Python (FastAPI) back end, React front end, a configurable price book, and AI powered by Claude, used only where it's safe. Claude reads report layouts the parsers don't recognize. It never does the math.

**Contents:** [Screenshots](#screenshots) · [What it does](#what-it-does) · [Quick start](#quick-start) · [Demo script](#demo-script-5-minutes) · [Project layout](#project-layout) · [Roadmap](#roadmap) · [Working with Claude Code](#working-with-claude-code) · [Contributing](#contributing)

![Estimate with material quantities, labor and recommended selling price](docs/screenshots/estimate.png)

![flow](docs/flow.svg)

## Screenshots

| Upload or try a sample | Verification blocks bad data |
|---|---|
| ![Upload page with sample reports and recent jobs](docs/screenshots/home.png) | ![Review page: missing eaves and pitch areas that don't add up block the estimate](docs/screenshots/review-blocked.png) |
| **Unknown formats are flagged for review** | **Formulas and prices live in the price book** |
| ![Review page: an unrecognized worksheet read by the generic parser and Claude, each value shown with its source text and confidence](docs/screenshots/review-unknown-format.png) | ![Price book with quantity formulas, coverage, waste and prices](docs/screenshots/pricebook.png) |

## What it does

| Step | What happens |
|------|--------------|
| **1. Upload** | Drop in a measurement PDF. The provider is detected from fingerprints in the text and parsed with that provider's template. |
| **2. Review** | Every value is shown next to the exact PDF text it came from, with its source (template / generic match / AI / edited) and confidence. Deterministic checks flag missing fields, pitch areas that don't add up, perimeter mismatches, low-slope roofs, and unconfirmed AI values. Errors block estimating. |
| **3. Estimate** | Material quantities come from price-book formulas (coverage, waste, round-up to purchasable units). Labor uses per-square rates plus steep-pitch charges from the area-by-pitch table. Quantities and prices are editable; edits are kept when formulas re-run; any line can be reset. Totals show cost, margin, selling price, and $/square. |
| **Price book** | Materials, coverage rules, labor rates, and assemblies (e.g. "Architectural re-roof", "Economy 3-tab") live in data, not code. |

## Quick start

Requirements: Python 3.11+ and Node 20+.

```bash
# back end
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m scripts.make_samples      # (re)generate the demo PDFs

# front end
cd ../frontend
npm install
```

**Development (hot reload):** `./dev.sh` → open http://localhost:5173

**Single-process demo:** `cd frontend && npm run build`, then `cd ../backend && .venv/bin/uvicorn app.main:app --port 8010` (add `--env-file .env` if you created one) → open http://localhost:8010

**Tests:** `cd backend && .venv/bin/python -m pytest`

### Optional: AI extraction

```bash
# in backend/.env (gitignored; ./dev.sh loads it):
ANTHROPIC_API_KEY=sk-ant-...
# or in your shell:
export ANTHROPIC_API_KEY=sk-ant-...
```

With a key set, reports in unknown formats are also read by Claude (`claude-opus-5-5` by default, override with `EXTRACTION_MODEL`), as long as "Use AI" is checked on upload. Without one, the app still works: unknown formats use the generic parser and the reviewer fills any gaps. Set `AI_EXTRACTION=off` to disable it explicitly.

To check the AI path against the real API (one API call): `cd backend && .venv/bin/python -m scripts.check_ai_live`. It reads the unknown-format sample and checks that AI fills only missing fields, quotes its source, flags numbers it can't find in the PDF text, and that the demo samples never call AI.

### Database

SQLite by default (`backend/data/estimateai.db`, created on first run). For PostgreSQL / Supabase, set `DATABASE_URL`, e.g. `postgresql+psycopg://user:pass@host:5432/estimateai`, and `pip install psycopg[binary]`.

## Demo script (5 minutes)

1. **Demo Provider A sample** → *Use sample*. All checks pass; every value shows its source line from the PDF. *Generate estimate*.
2. On the estimate, click **Architectural laminated shingles** to see the math: `2,846 sq ft × 1.12 waste ÷ 33.333 = 95.63 → 96 bundles`. Change waste to 15% (quantities re-run), override a quantity (marked *Edited*, survives re-runs), change margin, and watch the price update.
3. **Demo Provider B sample**: a different layout with areas in *squares* and `9:12` pitch notation, normalized automatically. Steep charges are priced per pitch band from the slope table, not just the predominant pitch.
4. **Report with problems**: estimating is blocked. Eaves are missing, and the pitch areas sum to 2,050 vs. 2,200 sq ft. Enter eaves, fix the pitch table, save → checks pass.
5. **Unknown format**: a free-text worksheet. The generic parser finds most values at lower confidence. With an API key, AI fills the rest. Every one must be confirmed before the warnings clear.
6. **Price book**: change a price; new estimates use it.

## About the sample reports

Roof measurement reports come from several aerial/satellite measurement companies, and each one lays out its PDF differently. The four bundled samples are **made up**: no real company's names, logos, layouts or customer data.

| Sample | What it shows |
|---|---|
| **Demo Provider A** (`demo_a_1428_maple_ave.pdf`) | A known layout with clean data: areas in sq ft, pitch as `6/12`, lengths with counts. Verifies straight through. |
| **Demo Provider B** (`demo_b_77_ridgeview_dr.pdf`) | A second known layout with different labels and units: areas in *squares*, pitch as `9:12`, a slope table across three pitches. |
| **Report with problems** (`demo_a_needs_review_oak_st.pdf`) | Provider A's layout with the eaves missing and pitch areas that don't add up. Verification blocks the estimate. |
| **Unknown format** (`field_worksheet_unknown_format.pdf`) | A free-text worksheet in no known layout. The generic parser and (optionally) AI read it, and every value is flagged for review. |

**How a report is read** (`backend/app/extraction/`):

1. **Detect the layout.** Each provider parser lists *fingerprints*, phrases that appear on every report of that layout and on no other. The first parser whose fingerprints are all in the PDF text wins.
2. **Template parse.** The matching parser reads each field with a pattern written for that layout, converts units in code (squares → sq ft, `9:12` → 9), and records the PDF line each value came from (confidence 0.98).
3. **No match:** the generic parser looks for common label wording in any text (confidence 0.70, needs confirmation). If fields are still missing, an API key is set and AI is enabled on upload, Claude reads only those, quoting where each came from. Numbers not found in the PDF text are flagged.
4. **Verification** then checks the result, whichever path produced it.

**Real providers.** A real provider's report works today through step 3, flagged for review. For reliable, fully automatic extraction, add a template parser from a real sample report: one small class in `providers/` plus a test in `tests/test_parsers.py`. The `provider-parser-builder` Claude Code agent does this from a sample PDF. Real report samples aren't committed to this repo, since they would contain customer data.

## Project layout

```
backend/
  app/
    extraction/
      providers/        one template parser per provider + generic parser (add new providers here)
      ai.py             Claude structured-output extraction for unknown layouts
      pipeline.py       template → generic → AI (missing fields only) → human review
    verification.py     deterministic measurement checks
    formula.py          safe Decimal expression evaluator for price-book formulas
    calculator.py       material / labor quantities, waste, steep-pitch bands
    services.py         reports, estimates, totals
    main.py             REST API (+ serves the built front end)
    config/pricebook.json   seed materials, labor rates, assemblies
  samples/              demo PDFs (fictional providers)
  scripts/make_samples.py
  tests/                parsers, verification, calculator, AI (mocked), API flow
frontend/src/
  pages/                Home (upload), Review, Estimate, Price book
docs/DESIGN.md          architecture and design decisions
```

## Roadmap

- **CRM integration:** push approved estimates and pull contacts/jobs through the contractor's CRM API.
- **Production handoff:** AI reviews the approved estimate against job notes, flags missing or conflicting details, and creates correction tasks. A production manager approves the final handoff.
- **More providers:** add a template parser per real provider once sample reports are available. Unknown layouts already work through the generic + AI path.
- **Multi-company:** per-company price books, branding, and users, for offering the platform as SaaS.
- **Customer-facing proposal:** branded PDF with good/better/best options.

Each item gets its own plan in [docs/plans/](docs/plans/README.md) when work starts.

## Working with Claude Code

The repo was built with [Claude Code](https://claude.com/claude-code) and ships the setup it used in `.claude/`. [CLAUDE.md](CLAUDE.md) holds the rules it follows.

| | |
|---|---|
| **Skills** | `/plan-task` writes a plan in `docs/plans/` and waits for approval · `/ship-plan` checks, commits, pushes and marks the plan Done |
| **Agents** | `test-runner` runs every check and explains failures · `code-reviewer` (read-only) checks changes against the project rules · `provider-parser-builder` adds a new measurement-report layout from a sample PDF, with tests |
| **Hooks** | After each edit, Python changes run the backend tests and TypeScript changes run the type-check. Before Claude finishes, the full check runs if code changed. At session start, the open plans are loaded |
| **CI** | GitHub Actions runs the same backend tests, type-check and build on every push and pull request |

A typical change: `/plan-task` (or plan mode), approve, build with tests, run `test-runner` and `code-reviewer`, then `/ship-plan`.

## Contributing

Read [CLAUDE.md](CLAUDE.md) for the rules: AI reads and code calculates, `Decimal` for money and quantities, formulas stay in the price book, every measurement keeps its source, and docs change in the same commit as the code they describe. Then see [docs/plans/](docs/plans/README.md) for how the project was built, plan by plan, including follow-ups. Architecture details are in [docs/DESIGN.md](docs/DESIGN.md).
