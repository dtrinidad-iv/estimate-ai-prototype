# 04 — README screenshots and repo topics

**Status:** Done
**Commits:** `991181b`

## Goal
Make the public repo read well as a portfolio piece.

## Decisions
- Shots come from the real app with a fresh DB and the bundled samples. Headless Chrome at 1440 wide, 2× scale, downscaled to 1600/1100 px and quantized with Pillow (about 660 KB total).
- The two review shots are cropped to the measurements column, because headless Chrome can't render the PDF iframe and leaves a dark box. Faking the PDF panel was rejected.
- Topics: fastapi, react, typescript, python, claude-api, ai, pdf-extraction, construction-tech, roofing, estimating, sqlalchemy, vite.

## README screenshots
- `docs/screenshots/estimate.png`: hero; estimate with summary and recommended price (AeroRoof sample).
- `docs/screenshots/home.png`: upload, samples, recent jobs.
- `docs/screenshots/review-blocked.png`: missing eaves and pitch areas that don't add up block the estimate.
- `docs/screenshots/review-unknown-format.png`: generic-parser values flagged for review, with source text.
- `docs/screenshots/pricebook.png`: formulas, coverage, waste, prices.

To retake: delete `backend/data/estimateai.db`, start on 8010, load the samples (worksheet, oak, maple, aeroroof, in that order), create estimates for reports 3 and 4, and capture `#/`, `#/report/2`, `#/report/1`, `#/estimate/2`, `#/pricebook`.
