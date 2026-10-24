#!/usr/bin/env bash
# SessionStart: give Claude the open tasks from PLAN.md so work resumes where it left off.
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
tasks=$(python3 "$ROOT/scripts/plan.py" 2>/dev/null)
[ -z "$tasks" ] && exit 0
jq -n --arg t "Open tasks from PLAN.md (number, status, name):
$tasks
Mark a task wip when you start it and done when its checks pass (python3 scripts/plan.py <status> <#>)." \
  '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $t}}'
