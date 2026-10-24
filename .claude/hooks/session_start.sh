#!/usr/bin/env bash
# SessionStart: give Claude the open plans from docs/plans/README.md so work resumes where it left off.
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
index="$ROOT/docs/plans/README.md"
[ -f "$index" ] || exit 0
open=$(grep -E '^\| *[0-9]+ *\|' "$index" | grep -viE '\| *Done *\| *$' | sed -E 's/^\| *([0-9]+) *\| *\[([^]]*)\]\(([^)]*)\) *\| *([^|]*[^ |]) *\| *$/\1 \4: \2 (docs\/plans\/\3)/')
[ -z "$open" ] && exit 0
jq -n --arg t "Open plans (docs/plans/README.md):
$open
Read a plan before continuing it. New work: plan first (/plan-task, or plan mode; on approval save it as the next docs/plans/NN-*.md with Status WIP)." \
  '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $t}}'
