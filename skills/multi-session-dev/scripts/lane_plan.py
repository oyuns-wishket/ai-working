#!/usr/bin/env python3
"""Validate a multi-session-dev lane plan and compute dependency waves.

Fails (not warns) on: overlapping write ownership, dependency cycles,
write lanes without a session/worktree, and write lanes when the caller's
input contract did not allow commits.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PLATFORMS = {"claude", "codex"}
MODES = {"session", "subagent"}
DEFAULT_MAX_PARALLEL = 3
DEFAULT_RETRY_LIMIT = 3


def load_plan(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, dict):
        raise SystemExit("lane plan must be a JSON object")
    return data


def lane_by_id(plan: dict[str, Any], lane_id: str) -> dict[str, Any]:
    for lane in plan.get("lanes", []):
        if lane.get("id") == lane_id:
            return lane
    raise SystemExit(f"lane not found in plan: {lane_id}")


def ownership_root(pattern: str) -> str:
    """Return the literal path prefix before the first glob character."""
    value = pattern.strip().lstrip("./")
    for marker in ("*", "?", "["):
        index = value.find(marker)
        if index != -1:
            value = value[:index]
    return value.rstrip("/")


def roots_overlap(a: str, b: str) -> bool:
    if a == b:
        return True
    if not a or not b:
        return True  # a bare "**" or "" owns everything
    return a.startswith(b + "/") or b.startswith(a + "/")


def compute_waves(lanes: list[dict[str, Any]]) -> tuple[list[list[str]], list[str]]:
    """Kahn levels. Returns (waves, errors)."""
    ids = [lane["id"] for lane in lanes]
    deps = {lane["id"]: list(lane.get("depends_on") or []) for lane in lanes}
    remaining = set(ids)
    done: set[str] = set()
    waves: list[list[str]] = []
    while remaining:
        ready = sorted(
            lane_id
            for lane_id in remaining
            if all(dep in done for dep in deps[lane_id])
        )
        if not ready:
            return waves, [f"dependency cycle among: {', '.join(sorted(remaining))}"]
        waves.append(ready)
        done.update(ready)
        remaining.difference_update(ready)
    return waves, []


def validate_plan(plan: dict[str, Any]) -> tuple[list[str], list[list[str]]]:
    errors: list[str] = []
    if plan.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    task = plan.get("task")
    if not isinstance(task, str) or not SLUG.fullmatch(task):
        errors.append("task must be lowercase kebab-case")
    target = plan.get("target_branch")
    if not isinstance(target, str) or not target.strip():
        errors.append("target_branch is required")
    elif target.strip() in {"main", "master", "develop", "production"}:
        errors.append(
            f"target_branch '{target}' is a shared branch; integrate into the Lead task branch instead"
        )
    if not isinstance(plan.get("commit_allowed"), bool):
        errors.append("commit_allowed must be boolean (from the caller's input contract)")
    max_parallel = plan.get("max_parallel", DEFAULT_MAX_PARALLEL)
    if not isinstance(max_parallel, int) or max_parallel < 1:
        errors.append("max_parallel must be a positive integer")

    lanes = plan.get("lanes")
    if not isinstance(lanes, list) or not lanes:
        errors.append("lanes must be a non-empty array")
        return errors, []

    seen: set[str] = set()
    for lane in lanes:
        if not isinstance(lane, dict):
            errors.append("each lane must be an object")
            continue
        lane_id = lane.get("id")
        if not isinstance(lane_id, str) or not SLUG.fullmatch(lane_id):
            errors.append(f"lane id must be lowercase kebab-case: {lane_id!r}")
            continue
        if lane_id in seen:
            errors.append(f"duplicate lane id: {lane_id}")
        seen.add(lane_id)
        for field in ("role", "acceptance"):
            if not isinstance(lane.get(field), str) or not lane[field].strip():
                errors.append(f"{lane_id}: {field} must be a non-empty string")
        if lane.get("mode") not in MODES:
            errors.append(f"{lane_id}: mode must be one of {sorted(MODES)}")
        if lane.get("platform") not in PLATFORMS:
            errors.append(f"{lane_id}: platform must be one of {sorted(PLATFORMS)}")
        write = lane.get("write")
        if not isinstance(write, bool):
            errors.append(f"{lane_id}: write must be boolean")
            continue
        if write:
            if lane.get("mode") != "session":
                errors.append(f"{lane_id}: write lanes must use mode 'session' (own worktree)")
            if not lane.get("owned_paths"):
                errors.append(f"{lane_id}: write lanes require non-empty owned_paths")
            if plan.get("commit_allowed") is False:
                errors.append(
                    f"{lane_id}: write lane requires commit_allowed=true; return blocked to the caller instead"
                )
            if lane.get("advisory"):
                errors.append(f"{lane_id}: advisory applies to read-only review lanes only")
        if not lane.get("prompt") and not lane.get("prompt_file"):
            errors.append(f"{lane_id}: prompt or prompt_file is required")
        if lane.get("prompt_file"):
            prompt_path = Path(lane["prompt_file"]).expanduser()
            if not prompt_path.is_absolute():
                prompt_path = Path(plan.get("repo") or ".") / prompt_path
            if not prompt_path.is_file():
                errors.append(f"{lane_id}: prompt_file not found: {lane['prompt_file']}")
        for dep in lane.get("depends_on") or []:
            if dep == lane_id:
                errors.append(f"{lane_id}: depends on itself")

    ids = {lane["id"] for lane in lanes if isinstance(lane.get("id"), str)}
    for lane in lanes:
        for dep in lane.get("depends_on") or []:
            if dep not in ids:
                errors.append(f"{lane.get('id')}: unknown dependency '{dep}'")

    write_lanes = [lane for lane in lanes if lane.get("write") is True]
    for index, first in enumerate(write_lanes):
        for second in write_lanes[index + 1 :]:
            for pattern_a in first.get("owned_paths") or []:
                for pattern_b in second.get("owned_paths") or []:
                    if roots_overlap(ownership_root(pattern_a), ownership_root(pattern_b)):
                        errors.append(
                            f"ownership overlap between write lanes '{first['id']}' ({pattern_a}) "
                            f"and '{second['id']}' ({pattern_b}); split the lanes or run them sequentially"
                        )

    if errors:
        return errors, []
    waves, cycle_errors = compute_waves(lanes)
    errors.extend(cycle_errors)
    return errors, ([] if cycle_errors else waves)


def summarize(plan: dict[str, Any], waves: list[list[str]]) -> dict[str, Any]:
    lanes = plan.get("lanes", [])
    return {
        "task": plan.get("task"),
        "target_branch": plan.get("target_branch"),
        "max_parallel": plan.get("max_parallel", DEFAULT_MAX_PARALLEL),
        "retry_limit": plan.get("retry_limit", DEFAULT_RETRY_LIMIT),
        "lane_count": len(lanes),
        "session_lanes": [l["id"] for l in lanes if l.get("mode") == "session"],
        "subagent_lanes": [l["id"] for l in lanes if l.get("mode") == "subagent"],
        "write_lanes": [l["id"] for l in lanes if l.get("write")],
        "advisory_lanes": [l["id"] for l in lanes if l.get("advisory")],
        "waves": waves,
    }


def command_validate(args: argparse.Namespace) -> int:
    plan = load_plan(Path(args.plan).expanduser())
    errors, waves = validate_plan(plan)
    payload = {"valid": not errors, "errors": errors, **summarize(plan, waves)}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("VALID" if not errors else "INVALID")
        for error in errors:
            print(f"- {error}")
        for index, wave in enumerate(waves):
            print(f"wave {index}: {', '.join(wave)}")
    return 0 if not errors else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a multi-session-dev lane plan.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--plan", required=True)
    validate.add_argument("--json", action="store_true")
    validate.set_defaults(func=command_validate)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
