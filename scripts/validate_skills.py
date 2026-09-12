#!/usr/bin/env python3
"""Validate skill frontmatter and local Markdown dependencies without third-party packages."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[[^]]*]\(([^)]+)\)")
NAME = re.compile(r"^[a-z0-9-]{1,64}$")


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        key, marker, value = line.partition(":")
        if marker and key.strip() in {"name", "description"}:
            values[key.strip()] = value.strip().strip("'\"")
    return values


def main() -> int:
    failures: list[str] = []
    skills = sorted(path for path in (ROOT / "skills").iterdir() if path.is_dir())
    for directory in skills:
        entrypoint = directory / "SKILL.md"
        if not entrypoint.is_file():
            failures.append(f"{directory.name}: missing SKILL.md")
            continue
        text = entrypoint.read_text()
        meta = frontmatter(text)
        if meta.get("name") != directory.name or not NAME.fullmatch(meta.get("name", "")):
            failures.append(f"{directory.name}: invalid or mismatched name")
        if not meta.get("description"):
            failures.append(f"{directory.name}: missing description")
        for source in directory.rglob("*.md"):
            if "assets" in source.relative_to(directory).parts or source.name.endswith(".template.md"):
                continue
            body = source.read_text(errors="replace")
            for raw in LINK.findall(body):
                target = raw.split("#", 1)[0].strip().strip("<>")
                if not target or "://" in target or target.startswith(("#", "/", "mailto:")) or any(c in target for c in "*$<>"):
                    continue
                if not (source.parent / target).resolve().exists():
                    failures.append(f"{source.relative_to(ROOT)}: missing link {target}")
    if failures:
        print("skill validation failed", file=sys.stderr)
        for failure in sorted(set(failures)):
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"skill validation passed: {len(skills)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
