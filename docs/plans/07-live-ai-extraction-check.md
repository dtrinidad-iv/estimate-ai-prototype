# 07 — Live check of AI extraction

**Status:** Done
**Commits:** `84542dd` (backend), `ee1c69e` (claude), `9488aa0` (docs)

## Goal
AI extraction has only ever run against the fake client (plan 01 follow-up). Run it against the real Claude API with the key now in `backend/.env`. Confirm the rules from CLAUDE.md hold on real output: AI fills only missing fields, stores verbatim quotes with `source="ai"`, lowers confidence when the number isn't in the PDF text, and verification flags its values for review. Fix whatever the live run shows is broken, and make the `.env` key actually reach the app.

Out of scope: prompt tuning beyond what a failure requires, new fields, AI for known templates (they never call AI, by design).

## Decisions
- **Load `backend/.env` with uvicorn's `--env-file .env`.** Nothing reads `.env` today, so a key there is ignored. `python-dotenv` is already installed through `uvicorn[standard]`, so no new dependency. `scripts/check_ai_live.py` imports it directly too; relying on it through `uvicorn[standard]` is deliberate. Shell `export` keeps working, since environment variables already set take precedence.
- **The live check is a script, not a pytest test.** CLAUDE.md says AI tests never touch the network. `scripts/check_ai_live.py` runs on demand, costs one API call (the unknown-format sample only), and exits non-zero if an invariant fails.
- **Samples:** `field_worksheet_unknown_format.pdf` is the real target, since only unknown layouts call AI. The three demo samples get one pass to confirm they still never call AI (a check on `method == "template"`, no API spend).
- **Record results in this plan** (fields filled, confidences, quotes, any not-in-text flags, model, latency), with no key or full response bodies.

## Backend (`backend/`)
- `scripts/check_ai_live.py`: refuses to run unless `ai_available()` (key or auth token set, `AI_EXTRACTION` not off); loads `.env` via `python-dotenv`. For the unknown-format sample, it runs `pipeline.run_extraction` and prints a table of key, value, source, confidence and evidence. It asserts:
  - AI keys are a subset of the fields the generic parser missed, and generic values are untouched.
  - Every AI value has `source == "ai"` and a non-empty quote.
  - Confidence is 0.8 when the number appears in the PDF text and 0.4 (with "[number not found in PDF text]") otherwise.
  - `result.method == "generic+ai"`.
  - Run through `verification`: every unconfirmed AI value produces a "read by AI" warning.
  - Each AI quote appears verbatim in the PDF text and contains the value's number. This is independent of `appears_in_text`, so a paraphrased or invented quote fails.
  - For the demo samples (exactly 3 must exist), `method == "template"`.
- `app/extraction/ai.py`: only changes the live run forces (none were needed; see Results). The likely spot is the `parse` call arguments (`betas`, `fallbacks`, `output_config`), which have never been exercised against the real API. Each fix gets a fake-client test.
- `dev.sh`: passes `--env-file .env` only when `backend/.env` exists. uvicorn refuses to start with a missing env file, so passing it unconditionally would break `./dev.sh` for anyone without a key.

## Frontend (`frontend/`)
None, unless the live run surfaces a display problem with AI evidence. That would be added to this plan before building.

## Tests
- `test_ai.py`: a fake-client test for each bug the live run finds (e.g. a request argument the API rejects, or a response shape not handled). No network. None were found, so no new tests.
- No new money or quantity math.

## README screenshots
Retake `review-unknown-format.png` with the key set. The old shot was taken without a key, so it showed "AI extraction skipped" and no AI value, and the README never showed the AI feature. Captured as in plan 04 (headless Chrome, 1440 wide at 2×, measurements column cropped, 1100 px, quantized) against a scratch DB through `DATABASE_URL`, so the local DB wasn't deleted. Only this shot changes; the others don't involve AI.

## Docs
- README "Optional: AI extraction": put the key in `backend/.env` (gitignored) or export it. Mention the "Use AI" upload checkbox, and how to run `scripts/check_ai_live.py`.
- CLAUDE.md commands table: add the live check, marked as costing API calls.
- Plan 01: mark the follow-up as done in plan 07.

## Results (2026-10-25)
The live run passed every check on the first try; `ai.py` needed no changes. The request arguments (`betas`, `fallbacks`, `output_config`, `output_format`) were accepted.

`field_worksheet_unknown_format.pdf`, model `claude-opus-5-5`, 6–13 s per call:
- The generic parser found 8 fields: area 1,980, pitch 7, ridges 64, hips 0, valleys 24, rakes 88, eaves 140, step flashing 16.
- AI filled the one remaining stated value: `wall_flashing_ft` = 6, confidence 0.80, quote "Chimney has 6 LF of apron flashing." Its number is in the PDF text, so it carries no not-found flag.
- AI returned null for facets, perimeter, reported squares and waste. None are stated in the worksheet, and it did not sum eaves + rakes into a perimeter. The pitch breakdown came back empty (the worksheet has no area-by-pitch table).
- The verification step raised exactly one "read by AI" warning, for wall flashing.
- All three demo samples: `method == "template"`, no API call.

Browser: the Review page shows "extracted by generic+ai", an "AI read · 80%" badge on wall flashing with its quote, and the "read by AI" check in the review list.

End to end: with `ANTHROPIC_API_KEY` unset in the shell, `uvicorn --env-file .env` reported `ai_enabled: true`. Loading the sample through `POST /api/samples/.../load` gave the same AI value and warning, and `can_estimate: true`.

## Follow-ups (not done)
- An AI `pitch_breakdown` isn't checked against the PDF text or given provenance the way field values are. It was empty here, so it was not exercised. Worth a fake-client test, plus a not-found check before a report with a pitch table goes through AI.
- AI values keep the float's form (`6.0` rather than `6`). The value is equal, so this is cosmetic.

## Verification
- `cd backend && .venv/bin/python -m scripts.check_ai_live` passes.
- Manual: `./dev.sh`, upload the unknown-format sample with AI on; the Review page shows AI badges, quotes and "read by AI" warnings.
- pytest, `tsc -b`, `npm run build`; `test-runner` and `code-reviewer` agents on the diff.

## Commits after approval
`feat(backend): ...` (script, fixes, dev.sh), `docs: ...`, then this plan → Done.
