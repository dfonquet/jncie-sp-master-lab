#!/usr/bin/env python3
"""Validate local Markdown links and key profile facts."""

from __future__ import annotations

import re
from pathlib import Path

from profiles import PROFILES, ROOT

LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def main() -> int:
    errors: list[str] = []
    for document in ROOT.rglob("*.md"):
        if any(part.startswith(".") or part in {"clab-"} for part in document.parts[len(ROOT.parts):]):
            continue
        text = document.read_text(encoding="utf-8")
        if not text.startswith("# "): errors.append(f"{document.relative_to(ROOT)}: missing H1")
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "#", "mailto:")): continue
            path = (document.parent / target.split("#", 1)[0]).resolve()
            if not path.exists(): errors.append(f"{document.relative_to(ROOT)}: broken link {target}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    normalized_readme = readme.replace("`", "")
    for profile in PROFILES.values():
        expected = f"| {profile.name} | {profile.expected_routers} |"
        if expected not in normalized_readme: errors.append(f"README: profile count missing for {profile.name}")
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors)); return 1
    print(f"PASS documentation: {len(list(ROOT.rglob('*.md')))} Markdown files, local links and profile facts")
    return 0


if __name__ == "__main__": raise SystemExit(main())
