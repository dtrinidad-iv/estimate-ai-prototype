# EstimateAI

Upload a roof measurement report → extract and verify the measurements → get a material & labor estimate with a recommended selling price.

A working prototype of an estimating platform for roofing contractors: Python (FastAPI) back end, React front end, a configurable price book, and AI used only where it's safe — reading unfamiliar report layouts, never doing the math.

![flow](docs/flow.svg)

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

**Single-process demo:** `cd frontend && npm run build`, then `cd ../backend && .venv/bin/uvicorn app.main:app --port 8010` → open http://localhost:8010

**Tests:** `cd backend && .venv/bin/python -m pytest`

### Optional: AI extraction

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

With a key set, reports in unknown formats are also read by Claude (`claude-opus-5-5` by default, override with `EXTRACTION_MODEL`). Without one, the app still works: unknown formats use the generic parser and the reviewer fills any gaps. Set `AI_EXTRACTION=off` to disable it explicitly.

### Database

SQLite by default (`backend/data/estimateai.db`, created on first run). For PostgreSQL / Supabase, set `DATABASE_URL`, e.g. `postgresql+psycopg://user:pass@host:5432/estimateai`, and `pip install psycopg[binary]`.

## Demo script (5 minutes)

1. **SkyMeasure Pro sample** → *Use sample*. All checks pass; every value shows its source line from the PDF. *Generate estimate*.
2. On the estimate, click **Architectural laminated shingles** to see the math: `2,846 sq ft × 1.12 waste ÷ 33.333 = 95.63 → 96 bundles`. Change waste to 15% (quantities re-run), override a quantity (marked *Edited*, survives re-runs), change margin, and watch the price update.
3. **AeroRoof sample**: a different layout with areas in *squares* and `9:12` pitch notation, normalized automatically. Steep charges are priced per pitch band from the slope table, not just the predominant pitch.
4. **Report with problems**: estimating is blocked. Eaves are missing, and the pitch areas sum to 2,050 vs. 2,200 sq ft. Enter eaves, fix the pitch table, save → checks pass.
5. **Unknown format**: a free-text worksheet. The generic parser finds most values at lower confidence. With an API key, AI fills the rest. Every one must be confirmed before the warnings clear.
6. **Price book**: change a price; new estimates use it.

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
