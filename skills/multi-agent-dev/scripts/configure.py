#!/usr/bin/env python3
"""Manage machine-local multi-agent-dev configuration."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
VALID_PLATFORMS = {"claude", "codex"}


def default_config_path() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "multi-agent-dev" / "config.json"


def empty_config() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "workspace_roots": [],
        "erp_domain_references": [],
        "worktree_root": None,
        "platforms": [],
    }


def normalize_path(value: str) -> str:
    return str(Path(value).expanduser().resolve(strict=False))


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_config()
    with path.open(encoding="utf-8") as stream:
        data = json.load(stream)
    merged = empty_config()
    merged.update(data)
    return merged


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def add_unique(items: list[str], values: list[str]) -> list[str]:
    result = list(items)
    for value in values:
        if value not in result:
            result.append(value)
    return result


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    for root in data.get("workspace_roots", []):
        path = Path(root)
        if not path.is_dir():
            errors.append(f"workspace root does not exist: {root}")

    for reference in data.get("erp_domain_references", []):
        path = Path(reference)
        if not path.is_file():
            errors.append(f"ERP domain reference does not exist: {reference}")

    worktree_root = data.get("worktree_root")
    if not worktree_root:
        errors.append("worktree_root is required for write-worker orchestration")
    else:
        path = Path(worktree_root)
        existing_parent = next((p for p in [path, *path.parents] if p.exists()), None)
        if existing_parent is None or not existing_parent.is_dir():
            errors.append(f"worktree root has no usable parent: {worktree_root}")

    platforms = set(data.get("platforms", []))
    if not platforms:
        errors.append("at least one platform is required")
    invalid = platforms - VALID_PLATFORMS
    if invalid:
        errors.append(f"invalid platforms: {', '.join(sorted(invalid))}")
    return errors


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def command_show(args: argparse.Namespace) -> int:
    path = Path(args.config).expanduser()
    data = load_config(path)
    payload = {"config_path": str(path), "exists": path.exists(), "config": data}
    if args.json:
        print_json(payload)
    else:
        print(f"Config: {path}")
        print(f"Exists: {'yes' if path.exists() else 'no'}")
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def command_set(args: argparse.Namespace) -> int:
    path = Path(args.config).expanduser()
    data = empty_config() if args.reset else load_config(path)

    workspace_roots = [normalize_path(value) for value in args.workspace_root]
    domain_references = [normalize_path(value) for value in args.erp_domain_reference]
    if args.replace_workspace_roots:
        data["workspace_roots"] = workspace_roots
    else:
        data["workspace_roots"] = add_unique(
            list(data.get("workspace_roots", [])), workspace_roots
        )
    if args.replace_erp_domain_references:
        data["erp_domain_references"] = domain_references
    else:
        data["erp_domain_references"] = add_unique(
            list(data.get("erp_domain_references", [])), domain_references
        )

    if args.worktree_root:
        data["worktree_root"] = normalize_path(args.worktree_root)

    requested_platforms: list[str] = []
    for platform in args.platform:
        requested_platforms.extend(
            ["claude", "codex"] if platform == "both" else [platform]
        )
    if args.replace_platforms:
        data["platforms"] = sorted(set(requested_platforms))
    elif requested_platforms:
        data["platforms"] = sorted(
            set(data.get("platforms", [])) | set(requested_platforms)
        )

    data["schema_version"] = SCHEMA_VERSION
    atomic_write(path, data)
    errors = validate(data)
    print_json(
        {
            "config_path": str(path),
            "saved": True,
            "valid": not errors,
            "errors": errors,
            "config": data,
        }
    )
    return 0


def command_validate(args: argparse.Namespace) -> int:
    path = Path(args.config).expanduser()
    data = load_config(path)
    errors = ["configuration file does not exist"] if not path.exists() else []
    errors.extend(validate(data))
    payload = {
        "config_path": str(path),
        "valid": not errors,
        "errors": errors,
        "config": data,
    }
    if args.json:
        print_json(payload)
    else:
        print("VALID" if not errors else "INVALID")
        for error in errors:
            print(f"- {error}")
    return 0 if not errors else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage machine-local multi-agent-dev configuration."
    )
    parser.add_argument("--config", default=str(default_config_path()))
    subparsers = parser.add_subparsers(dest="command", required=True)

    show = subparsers.add_parser("show")
    show.add_argument("--json", action="store_true")
    show.set_defaults(func=command_show)

    set_parser = subparsers.add_parser("set")
    set_parser.add_argument("--workspace-root", action="append", default=[])
    set_parser.add_argument("--erp-domain-reference", action="append", default=[])
    set_parser.add_argument("--worktree-root")
    set_parser.add_argument(
        "--platform",
        action="append",
        choices=["claude", "codex", "both"],
        default=[],
    )
    set_parser.add_argument("--replace-workspace-roots", action="store_true")
    set_parser.add_argument("--replace-erp-domain-references", action="store_true")
    set_parser.add_argument("--replace-platforms", action="store_true")
    set_parser.add_argument("--reset", action="store_true")
    set_parser.set_defaults(func=command_set)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--json", action="store_true")
    validate_parser.set_defaults(func=command_validate)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
