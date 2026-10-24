# 06 — Neutral demo provider names + README explanation

**Status:** Done
**Commits:** `315109d` (backend), `a2d9599` (frontend), `a72be36` (claude), `b149c22` (docs)

## Goal
The two sample report layouts were given invented brand-like names ("SkyMeasure Pro", "AeroRoof Analytics"). Nobody checked whether those names already belong to real companies, and the repo is public and shown to clients. Rename them to obviously fictional names, and explain in the README what the sample providers are and how real providers get added.

Out of scope: parsers for real providers (needs real sample reports from a client).

## Decisions
- New names: **Demo Provider A** (key `demo_a`; was SkyMeasure: sq ft areas, `x/12` pitch) and **Demo Provider B** (key `demo_b`; was AeroRoof: areas in squares, `x:12` pitch, different labels). Plain names make it obvious they aren't real companies, and the layouts stay as different as before.
- Fingerprints: `DEMO PROVIDER A` + `Report Summary`, and `DEMO PROVIDER B` + `Roof Geometry Summary`.
- Sample files: `demo_a_1428_maple_ave.pdf`, `demo_b_77_ridgeview_dr.pdf`, `demo_a_needs_review_oak_st.pdf`; `field_worksheet_unknown_format.pdf` is unchanged. PDFs regenerated, old ones deleted.
- Report numbers `SM-…`/`AR-…` become `DA-…`/`DB-…`.
- Plan 01 keeps its historical wording, with a note pointing here. The old names stay in git history; that can't be changed without rewriting pushed commits.

## Backend (`backend/`)
- `app/extraction/providers/skymeasure.py` → `demo_a.py` (`DemoProviderAParser`), `aeroroof.py` → `demo_b.py` (`DemoProviderBParser`); registry in `providers/__init__.py`.
- `scripts/make_samples.py`: functions, titles, footers, file names.
- `samples/`: regenerated.

## Frontend (`frontend/`)
- `src/pages/HomePage.tsx`: sample file names and titles in `SAMPLE_INFO`.

## Tests
`test_parsers.py`, `test_api.py`, `test_ai.py`: new file names and provider keys. Same assertions otherwise.

## Docs
- README: demo script names, plus a new "About the sample reports" section. It covers what the demo providers are, why they're fictional, what happens with a real provider's report (generic parser + AI, flagged for review), and how to add a real provider (one parser + a test, or the `provider-parser-builder` agent).
- CLAUDE.md "Generic branding" rule, plan 04 retake steps, the `provider-parser-builder` agent's example file names.

## README screenshots
Retake all five; the home, review and estimate shots show the old names. Same process as plan 04.

## Verification
pytest, `tsc -b`, build; `git grep -i -e skymeasure -e aeroroof` returns only plan 01's history note and this plan.

## Commits after approval
`refactor(backend): ...`, `refactor(frontend): ...`, `docs: ...`, then this plan → Done.

## Follow-ups (not done)
- Fingerprints are case-insensitive substrings, so `DEMO PROVIDER A` would also match e.g. "Demo Provider Alpha". Consider a third, more specific fingerprint (e.g. "Areas per Pitch") if another similar layout is added.
