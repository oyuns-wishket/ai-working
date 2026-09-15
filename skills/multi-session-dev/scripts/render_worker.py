#!/usr/bin/env python3
"""Render project worker definitions for Claude and Codex from one JSON spec."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VALID_EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}


def git_root(project: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"Not a Git project: {project}\n{result.stderr.strip()}")
    return Path(result.stdout.strip()).resolve()


def load_spec(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, dict):
        raise SystemExit("Worker spec must be a JSON object")
    return data


def validate_spec(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    name = data.get("name")
    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
        errors.append("name must be lowercase kebab-case")
    for field in ("description", "capability", "instructions"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if not isinstance(data.get("write_access"), bool):
        errors.append("write_access must be boolean")
    if "command_access" in data and not isinstance(data.get("command_access"), bool):
        errors.append("command_access must be boolean when present")
    effort = data.get("codex_reasoning_effort", "high")
    if effort not in VALID_EFFORTS:
        errors.append(
            f"codex_reasoning_effort must be one of {', '.join(sorted(VALID_EFFORTS))}"
        )
    references = data.get("required_references", [])
    if not isinstance(references, list) or not all(
        isinstance(value, str) for value in references
    ):
        errors.append("required_references must be a list of strings")
    return errors


def common_instructions(data: dict[str, Any]) -> str:
    references = data.get("required_references", [])
    reference_text = ""
    if references:
        joined = ", ".join(f"`{value}`" for value in references)
        reference_text = f"\n\nBefore work, read these repo-relative references when they exist: {joined}."
    return (
        data["instructions"].strip()
        + reference_text
        + "\n\nDo not spawn nested subagents. Return STATUS, SCOPE, FILES, "
        "EVIDENCE, RISKS, and HANDOFF to the Lead."
    )


def render_claude(data: dict[str, Any]) -> str:
    tools = ["Read", "Grep", "Glob"]
    if data.get("command_access") or data["write_access"]:
        tools.append("Bash")
    if data["write_access"]:
        tools.extend(["Write", "Edit"])
    lines = [
        "---",
        f"name: {data['name']}",
        f"description: {json.dumps(data['description'], ensure_ascii=False)}",
        "tools:",
        *[f"  - {tool}" for tool in tools],
        "---",
        "",
        common_instructions(data),
        "",
    ]
    return "\n".join(lines)


def render_codex(data: dict[str, Any]) -> str:
    effort = data.get("codex_reasoning_effort", "high")
    sandbox = "workspace-write" if data["write_access"] else "read-only"
    instructions = common_instructions(data)
    return "\n".join(
        [
            f"name = {json.dumps(data['name'], ensure_ascii=False)}",
            f"description = {json.dumps(data['description'], ensure_ascii=False)}",
            f"model_reasoning_effort = {json.dumps(effort)}",
            f"sandbox_mode = {json.dumps(sandbox)}",
            f"developer_instructions = {json.dumps(instructions, ensure_ascii=False)}",
            "",
        ]
    )


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def planned_write(
    path: Path, content: str, force: bool, dry_run: bool
) -> dict[str, Any]:
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing == content:
        return {"path": str(path), "action": "unchanged"}
    if existing is not None and not force:
        raise SystemExit(
            f"Refusing to overwrite existing worker file without approval: {path}"
        )
    action = "replace" if existing is not None else "create"
    if not dry_run:
        atomic_write(path, content)
    return {"path": str(path), "action": action}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render Claude and Codex worker adapters from one JSON spec."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument(
        "--platform", choices=["claude", "codex", "both"], default="both"
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = git_root(Path(args.project).expanduser())
    source_spec = load_spec(Path(args.spec).expanduser())
    errors = validate_spec(source_spec)
    if errors:
        raise SystemExit("Invalid Worker spec:\n- " + "\n- ".join(errors))

    canonical = dict(source_spec)
    canonical["schema_version"] = 1
    canonical_content = (
        json.dumps(canonical, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    name = canonical["name"]
    writes: list[dict[str, Any]] = []
    writes.append(
        planned_write(
            root / ".agents" / "multi-session-dev" / "workers" / f"{name}.json",
            canonical_content,
            args.force,
            args.dry_run,
        )
    )
    if args.platform in {"claude", "both"}:
        writes.append(
            planned_write(
                root / ".claude" / "agents" / f"{name}.md",
                render_claude(canonical),
                args.force,
                args.dry_run,
            )
        )
    if args.platform in {"codex", "both"}:
        writes.append(
            planned_write(
                root / ".codex" / "agents" / f"{name}.toml",
                render_codex(canonical),
                args.force,
                args.dry_run,
            )
        )

    print(
        json.dumps(
            {
                "project": str(root),
                "worker": name,
                "dry_run": args.dry_run,
                "writes": writes,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
