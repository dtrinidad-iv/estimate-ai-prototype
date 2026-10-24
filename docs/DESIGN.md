# Design notes

## The core rule: AI reads, code calculates

Estimates are money. A wrong bundle count or a margin computed by a language model is unacceptable, so the system is split:

| Concern | Done by | Why |
|---|---|---|
| Reading known report layouts | Template parsers (regex per provider) | Fast, free, deterministic, ~100% accurate on a known layout |
| Reading unknown layouts | Generic label parser, then Claude for what's still missing | Flexible; output is treated as a *suggestion* |
| Unit conversion (squares → sq ft, `9:12` → 9) | Code | The model is told to copy values *as printed* |
| Checks and cross-checks | Code (`verification.py`) | Repeatable, explainable rules |
| Quantities, waste, rounding, pricing, margin | Code with `Decimal` (`calculator.py`, `services.py`) | Exact and auditable. Every line shows its formula |
| Final say | A person | Low-confidence values must be confirmed; edits are tracked |

## Extraction pipeline

```
PDF ──► text layer (pdfplumber)
          │
          ├─ provider fingerprint matches? ──► template parser (confidence 0.98)
          │
          └─ no ──► generic label parser (0.70)
                      └─ fields still missing + AI enabled ──► Claude structured output
                                                              (only for missing fields)
                                                              number found in PDF text? 0.8 : 0.4
```

- **Providers are plugins.** `ProviderParser` subclasses declare `fingerprints` and a `patterns` map of field → regex. Supporting a new provider means adding one small class and one sample-based test.
- **Normalized schema.** Every parser outputs the same fields (`fields.py`): area, pitch, facets, ridge/hip/valley/rake/eave lengths, flashing, perimeter, reported squares, suggested waste, and area by pitch.
- **Provenance per value.** Each measurement stores its value, original extracted value, source, confidence, the PDF snippet it came from, and whether a reviewer confirmed it.
- **AI guardrails.** The model returns JSON validated against a Pydantic schema (structured outputs). It must quote the text each value came from and return null rather than compute. Each returned number is then checked against the PDF's own text. If it doesn't appear there, confidence drops to 0.4 and the reviewer sees "number not found in PDF text". AI is never used on a layout that has a template. Server-side refusal fallbacks are enabled, so a declined request is retried automatically.

## Verification rules

Errors (block the estimate):
- Required field missing (area, pitch, ridges, rakes, eaves)
- Negative lengths, non-positive area, pitch outside 0–24/12
- Area-by-pitch total more than 5% off the total area
- Zero eaves on a pitched roof

Warnings (shown, allowed):
- Area-by-pitch total 1–5% off
- Reported squares ≠ area / 100
- Eaves + rakes ≠ reported perimeter (> 2%)
- Predominant pitch ≠ the pitch with the most area
- Perimeter implausibly short for the area (geometric lower bound)
- Low slope (< 4/12 double underlayment; < 2/12 not rated for shingles)
- Values from the generic parser or AI that haven't been confirmed

## Quantity formulas

Each material in the price book has:

```
qty = ceil( basis × (1 + waste%) ÷ coverage_per_unit )
```

`basis` is an expression over measurement fields, e.g. `eaves_ft * 2 + valleys_ft` for ice & water shield (two courses at the eaves, one in valleys). Expressions are evaluated by a small AST-based evaluator (`formula.py`) that allows only arithmetic, comparisons, `if/else`, `min`/`max`. There is no `eval`, no attribute access, and no function calls beyond those. Waste is either the job's waste % or a fixed per-material %.

The job waste % defaults to the report's suggestion. Otherwise it scales with roof complexity: hip + valley feet per square → 10 / 12 / 15%.

Steep-slope labor is priced per pitch band using the area-by-pitch table (8–9/12, 10–12/12, > 12/12). The whole roof is not charged at the predominant pitch.

## Pricing

```
cost  = materials + material tax + labor + other (dumpster, permit…)
price = cost ÷ (1 − target margin), rounded up to the next $10
```

Margin is on the selling price, not markup on cost. This is the most common source of underpricing.

## Data model

`jobs` → `reports` (uploaded PDF, provider, method, raw text, pitch breakdown, notes) → `measurements` (per field, with provenance).
`estimates` (assembly, waste, margin, tax) → `line_items` (calc qty vs. used qty, unit cost, formula text, overridden flag).
`materials`, `labor_rates`, `assemblies` form the price book.

SQLAlchemy 2.0 models run on SQLite locally and on PostgreSQL/Supabase via `DATABASE_URL`.
