#!/usr/bin/env bash
# Stop: before Claude finishes, run the full check if code changed since the last green run.
# Catches edits made through Bash (sed, heredocs) that the PostToolUse hook doesn't see.
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
input=$(cat)
[ "$(echo "$input" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0

stamp_file="$ROOT/.claude/.last-green"
stamp=$(find "$ROOT/backend/app" "$ROOT/backend/tests" "$ROOT/frontend/src" \
          -type f \( -name '*.py' -o -name '*.json' -o -name '*.ts' -o -name '*.tsx' \) \
          -newer "$stamp_file" 2>/dev/null | head -1)
if [ ! -f "$stamp_file" ] || [ -n "$stamp" ]; then
  backend=$(cd "$ROOT/backend" && .venv/bin/python -m pytest -q -p no:cacheprovider 2>&1); b=$?
  frontend=$(cd "$ROOT/frontend" && npx --no-install tsc -b 2>&1); f=$?
  if [ $b -ne 0 ] || [ $f -ne 0 ]; then
    reason="Checks failed. Fix before finishing."
    [ $b -ne 0 ] && reason="$reason
--- backend tests ---
$(echo "$backend" | tail -30)"
    [ $f -ne 0 ] && reason="$reason
--- frontend type-check ---
$(echo "$frontend" | head -30)"
    jq -n --arg r "$reason" '{decision: "block", reason: $r}'
    exit 0
  fi
  touch "$stamp_file"
fi
exit 0
