#!/usr/bin/env python3
"""Audit shared engine diffs for game-specific symbols and preprocessor guards.

The audit compares the working tree with a git base revision. It is intentionally
small and conservative: terms are maintained here when a generic-sounding name
still belongs to one game's implementation.

Examples:
  python3 tools/engine_boundary_audit.py
  python3 tools/engine_boundary_audit.py --base origin/main
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARED_PATHS = ("client", "common", "renderer", "server")
GAME_TERMS = {
    "WC3": ("gold", "lumber", "goldmine", "gold_mine"),
    "SC2": ("minerals", "vespene"),
    "WOW": ("talent", "talent_points"),
}
GAME_TERM_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:" + "|".join(
        re.escape(term) for terms in GAME_TERMS.values() for term in terms
    ) + r")(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
GAME_GUARD_RE = re.compile(r"^\+\s*#\s*ifdef\s+(WC3|SC2|WOW)\b")
ADDED_LINE_RE = re.compile(r"^\+(?!\+)")


def git_diff(base_revision: str) -> str:
    command = ["git", "diff", "--no-color", "--unified=0", base_revision, "--", *SHARED_PATHS]
    result = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git diff failed")
    return result.stdout


def audit(diff: str) -> list[str]:
    violations = []
    for line in diff.splitlines():
        if not ADDED_LINE_RE.match(line):
            continue
        content = line[1:]
        guard_match = GAME_GUARD_RE.match(line)
        if guard_match:
            violations.append(f"new #ifdef {guard_match.group(1)} guard: {content.strip()}")
        for match in GAME_TERM_RE.finditer(content):
            term = match.group(0)
            violations.append(f"game-specific term {term!r} in added shared-engine line: {content.strip()}")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="main", help="git revision to compare against (default: main)")
    args = parser.parse_args()
    try:
        violations = audit(git_diff(args.base))
    except RuntimeError as error:
        print(f"engine-boundary-audit: {error}", file=sys.stderr)
        return 2
    if violations:
        print("engine-boundary-audit: violations found:")
        for violation in violations:
            print(f"  {violation}")
        return 1
    print(f"engine-boundary-audit: clean against {args.base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
