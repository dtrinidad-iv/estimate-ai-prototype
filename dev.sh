#!/usr/bin/env bash
# Starts the API (port 8010) and the React dev server (port 5173) together.
set -e
cd "$(dirname "$0")"
# backend/.env (gitignored) holds ANTHROPIC_API_KEY; uvicorn refuses a missing --env-file.
ENV_ARGS=()
[ -f backend/.env ] && ENV_ARGS=(--env-file .env)
(cd backend && .venv/bin/uvicorn app.main:app --reload --port 8010 "${ENV_ARGS[@]}") &
API_PID=$!
trap 'kill $API_PID' EXIT
cd frontend && npm run dev
