#!/usr/bin/env bash
# Starts the API (port 8010) and the React dev server (port 5173) together.
set -e
cd "$(dirname "$0")"
(cd backend && .venv/bin/uvicorn app.main:app --reload --port 8010) &
API_PID=$!
trap 'kill $API_PID' EXIT
cd frontend && npm run dev
