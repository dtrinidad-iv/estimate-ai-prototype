# 03 — Git, GitHub and CI

**Status:** Done
**Commits:** `20f77fd` (initial commit), `c492ee1` (ci)

## Goal
Put the project under version control, publish it as a portfolio repo, and run the checks on every push.

Out of scope: branch protection, deployment.

## Decisions
- `main` branch; `.gitignore` excludes `.venv`, `node_modules`, `dist`, the SQLite DB, uploads, `.env`, and the hook marker file. Scanned for secrets before the first commit (only the README placeholder `sk-ant-...`).
- GitHub repo `dtrinidad-iv/estimate-ai-prototype`: created private, made **public** at the user's request after scanning all commits for client-identifying names (none found).
- `.github/workflows/ci.yml`: a `backend` job (Python 3.13, pip cache, pytest) and a `frontend` job (Node 20, npm cache, `npm ci`, `tsc -b`, build), on push to `main` and on pull requests.

## Verification
First CI run green on both jobs (run 40053704132).
