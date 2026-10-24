#!/usr/bin/env bash
# PostToolUse (Write|Edit): fast feedback on the file that was just changed.
#   backend Python / price book  -> pytest (stop at first failure)
#   frontend TypeScript          -> tsc type-check
# Exit 2 sends the failure back to Claude so it fixes it right away.
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
file=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')

case "$file" in
  "$ROOT"/backend/*.py|"$ROOT"/backend/app/config/*.json)
    out=$(cd "$ROOT/backend" && .venv/bin/python -m pytest -q -x -p no:cacheprovider 2>&1)
    if [ $? -ne 0 ]; then
      echo "Backend tests failed after editing ${file#$ROOT/}:" >&2
      echo "$out" | tail -40 >&2
      exit 2
    fi
    ;;
  "$ROOT"/frontend/src/*.ts|"$ROOT"/frontend/src/*.tsx)
    out=$(cd "$ROOT/frontend" && npx --no-install tsc -b 2>&1)
    if [ $? -ne 0 ]; then
      echo "TypeScript errors after editing ${file#$ROOT/}:" >&2
      echo "$out" | head -40 >&2
      exit 2
    fi
    ;;
esac
exit 0
