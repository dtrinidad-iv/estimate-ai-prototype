#!/usr/bin/env python3
"""Tiny tracker for PLAN.md task tables.

  python3 scripts/plan.py                 # show open (pending/wip) tasks
  python3 scripts/plan.py all             # show every task
  python3 scripts/plan.py wip 17          # set status (pending | wip | done | blocked)
  python3 scripts/plan.py done 17 18
  python3 scripts/plan.py add "Phase 2" "Task name" "Description"
"""

import re
import sys
from pathlib import Path

PLAN = Path(__file__).resolve().parent.parent / "PLAN.md"
STATUSES = {"pending", "wip", "done", "blocked"}
ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(pending|wip|done|blocked)\s*\|\s*$")


def rows(lines):
    for i, line in enumerate(lines):
        m = ROW.match(line)
        if m:
            yield i, int(m.group(1)), m.group(2), m.group(3), m.group(4)


def show(only_open: bool) -> None:
    lines = PLAN.read_text().splitlines()
    found = [r for r in rows(lines) if not only_open or r[4] in ("pending", "wip", "blocked")]
    if not found:
        print("No open tasks." if only_open else "No tasks.")
    for _, num, name, _, status in found:
        print(f"{num:>3}  {status:<8} {name}")


def set_status(status: str, nums: list[int]) -> None:
    lines = PLAN.read_text().splitlines()
    hit = set()
    for i, num, name, desc, _ in list(rows(lines)):
        if num in nums:
            lines[i] = f"| {num:<2} | {name} | {desc} | {status} |"
            hit.add(num)
    missing = set(nums) - hit
    if missing:
        sys.exit(f"Unknown task number(s): {sorted(missing)}")
    PLAN.write_text("\n".join(lines) + "\n")
    show(only_open=False)


def add(section: str, name: str, desc: str) -> None:
    lines = PLAN.read_text().splitlines()
    next_num = max((r[1] for r in rows(lines)), default=0) + 1
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith("## ") and section.lower() in l.lower())
    except StopIteration:
        sys.exit(f"No '## ...{section}...' heading in PLAN.md")
    insert_at = start + 1
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            break
        if lines[i].startswith("|"):
            insert_at = i + 1
    lines.insert(insert_at, f"| {next_num:<2} | {name} | {desc} | pending |")
    PLAN.write_text("\n".join(lines) + "\n")
    print(f"Added task {next_num}: {name}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        show(only_open=True)
    elif args[0] == "all":
        show(only_open=False)
    elif args[0] in STATUSES:
        set_status(args[0], [int(n) for n in args[1:]])
    elif args[0] == "add" and len(args) == 4:
        add(*args[1:])
    else:
        sys.exit(__doc__)
