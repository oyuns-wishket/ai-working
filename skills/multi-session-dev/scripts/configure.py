#!/usr/bin/env python3
"""Manage machine-local multi-session-dev configuration."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
VALID_PLATFORMS = {"claude", "codex"}


LEGACY_DIR_NAME = "multi-agent-dev"
VALID_ROLE_KEYS = {"claude_model", "claude_effort", "codex_model", "codex_effort"}


def default_config_path() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "multi-session-dev" / "config.json"


def legacy_config_path(path: Path) -> Path:
    return path.parent.parent / LEGACY_DIR_NAME / path.name


def empty_config() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "workspace_roots": [],
        "erp_domain_references": [],
        "worktree_root": None,
        "platforms": [],
        "max_parallel": 3,
        "retry_limit": 3,
        "max_budget_usd": None,
        "role_defaults": {},
        "binaries": {},
    }


def normalize_path(value: str) -> str:
    return str(Path(value).expanduser().resolve(strict=False))


def load_config(path: Path) -> dict[str, Any]:
    """Load the machine-local config; fall back to the retired multi-agent-dev file."""
    source = path if path.exists() else legacy_config_path(path)
    if not source.exists():
        return empty_config()
    with source.open(encoding="utf-8") as stream:
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

    for key in ("max_parallel", "retry_limit"):
        value = data.get(key)
        if value is not None and (not isinstance(value, int) or value < (1 if key == "max_parallel" else 0)):
            errors.append(f"{key} must be a non-negative integer (max_parallel >= 1)")
    budget = data.get("max_budget_usd")
    if budget is not None and (not isinstance(budget, (int, float)) or budget <= 0):
        errors.append("max_budget_usd must be a positive number")
    role_defaults = data.get("role_defaults") or {}
    if not isinstance(role_defaults, dict):
        errors.append("role_defaults must be an object keyed by role")
    else:
        for role, values in role_defaults.items():
            if not isinstance(values, dict):
                errors.append(f"role_defaults.{role} must be an object")
                continue
            unknown = set(values) - VALID_ROLE_KEYS
            if unknown:
                errors.append(f"role_defaults.{role} has unknown keys: {', '.join(sorted(unknown))}")
    binaries = data.get("binaries") or {}
    for name, value in binaries.items():
        if name not in VALID_PLATFORMS:
            errors.append(f"binaries.{name} is not a supported platform")
        elif not Path(str(value)).expanduser().is_file():
            errors.append(f"binaries.{name} does not exist: {value}")
    return errors


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def command_show(args: argparse.Namespace) -> int:
    path = Path(args.config).expanduser()
    data = load_config(path)
    legacy = legacy_config_path(path)
    payload = {
        "config_path": str(path),
        "exists": path.exists(),
        "legacy_config_path": str(legacy) if not path.exists() and legacy.exists() else None,
        "config": data,
    }
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
    if args.max_parallel is not None:
        data["max_parallel"] = args.max_parallel
    if args.retry_limit is not None:
        data["retry_limit"] = args.retry_limit
    if args.max_budget_usd is not None:
        data["max_budget_usd"] = args.max_budget_usd
    for entry in args.role_default:
        # format: <role>:<key>=<value>, e.g. reviewer:claude_model=opus or "*:codex_effort=high"
        try:
            role, rest = entry.split(":", 1)
            key, value = rest.split("=", 1)
        except ValueError as error:
            raise SystemExit(f"--role-default expects <role>:<key>=<value>, got {entry!r}") from error
        data.setdefault("role_defaults", {}).setdefault(role, {})[key] = value
    for entry in args.binary:
        try:
            name, value = entry.split("=", 1)
        except ValueError as error:
            raise SystemExit(f"--binary expects <platform>=<path>, got {entry!r}") from error
        data.setdefault("binaries", {})[name] = normalize_path(value)

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
        description="Manage machine-local multi-session-dev configuration."
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
    set_parser.add_argument("--max-parallel", type=int)
    set_parser.add_argument("--retry-limit", type=int)
    set_parser.add_argument("--max-budget-usd", type=float)
    set_parser.add_argument("--role-default", action="append", default=[])
    set_parser.add_argument("--binary", action="append", default=[])
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
