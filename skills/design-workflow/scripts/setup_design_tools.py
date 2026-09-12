#!/usr/bin/env python3
"""Plan or install project-local design skills for Claude Code and Codex."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


MINIMUM_NODE = (22, 12, 0)
SKILLS_CLI_VERSION = "1.5.20"
IMPECCABLE_VERSION = "3.4.0"
TASTE_SOURCE = "https://github.com/Leonxlnx/taste-skill"
MODE_SKILLS = {
    "new": "design-taste-frontend",
    "rebrand": "redesign-existing-projects",
    "refactor": "redesign-existing-projects",
    "small-feature": None,
    "audit": None,
}


def parse_version(raw: str) -> tuple[int, int, int]:
    match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", raw)
    if not match:
        raise ValueError(f"Unable to parse Node.js version: {raw.strip()}")
    return tuple(int(part) for part in match.groups())


def command_text(command: list[str]) -> str:
    return shlex.join(command)


def run(command: list[str], cwd: Path) -> dict[str, object]:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    evidence = {
        "command": command_text(command),
        "exit_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: "
            f"{command_text(command)}\n{detail}"
        )
    return evidence


def skill_state(project: Path, skill: str) -> dict[str, object]:
    paths = {
        "claude": project / ".claude" / "skills" / skill,
        "codex": project / ".agents" / "skills" / skill,
    }
    present = {provider: path.is_dir() for provider, path in paths.items()}
    return {
        "skill": skill,
        "paths": {provider: str(path) for provider, path in paths.items()},
        "present": present,
        "complete": all(present.values()),
        "partial": any(present.values()) and not all(present.values()),
    }


def build_plan(args: argparse.Namespace) -> dict[str, object]:
    project = args.project.expanduser().resolve()
    if not project.is_dir():
        raise ValueError(f"Project directory does not exist: {project}")

    node = shutil.which("node")
    npx = shutil.which("npx")
    if not node or not npx:
        raise ValueError("Node.js and npx are required")

    node_output = subprocess.run(
        [node, "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    node_version = parse_version(node_output)
    if node_version < MINIMUM_NODE:
        required = ".".join(str(part) for part in MINIMUM_NODE)
        raise ValueError(f"Node.js {required}+ is required; found {node_output}")

    git_result = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if git_result.returncode != 0:
        raise ValueError(f"Project is not inside a Git repository: {project}")
    git_root = Path(git_result.stdout.strip()).resolve()
    if git_root != project:
        raise ValueError(
            f"Pass the Git project root instead of a nested directory: {git_root}"
        )

    selected_skill = MODE_SKILLS[args.mode]
    if args.taste_skill == "none":
        selected_skill = None
    elif args.taste_skill:
        selected_skill = args.taste_skill

    states = [skill_state(project, "impeccable")]
    if selected_skill:
        states.insert(0, skill_state(project, selected_skill))

    partial = [state["skill"] for state in states if state["partial"]]
    if partial:
        names = ", ".join(str(name) for name in partial)
        raise ValueError(
            f"Partial provider installation detected for: {names}. "
            "Review the Claude/Codex directories and reconcile them without overwrite."
        )

    commands: list[dict[str, object]] = []
    if selected_skill and not states[0]["complete"]:
        taste_command = [
            npx,
            "--yes",
            f"skills@{args.skills_version}",
            "add",
            TASTE_SOURCE,
            "--skill",
            selected_skill,
            "--agent",
            "claude-code",
            "codex",
            "--yes",
            "--copy",
        ]
        commands.append(
            {
                "name": "taste",
                "command": taste_command,
                "display": command_text(taste_command),
            }
        )

    impeccable_state = next(
        state for state in states if state["skill"] == "impeccable"
    )
    if not impeccable_state["complete"]:
        impeccable_command = [
            npx,
            "--yes",
            f"impeccable@{args.impeccable_version}",
            "skills",
            "install",
            "-y",
            "--providers=claude,codex",
            "--scope=project",
        ]
        commands.append(
            {
                "name": "impeccable",
                "command": impeccable_command,
                "display": command_text(impeccable_command),
            }
        )

    return {
        "project": str(project),
        "git_root": str(git_root),
        "mode": args.mode,
        "taste_skill": selected_skill,
        "node": node_output,
        "apply": args.apply,
        "states_before": states,
        "commands": commands,
        "expected_files": [
            ".claude/skills/",
            ".agents/skills/",
            "skills-lock.json",
            ".claude/settings.local.json",
            ".codex/hooks.json",
        ],
        "warnings": [
            "Project-local skills can execute with full agent permissions; review installed files.",
            "Existing files and hook manifests must be inspected in the Git diff.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan or install project-local design tools for Claude and Codex."
    )
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--mode", choices=sorted(MODE_SKILLS), required=True)
    parser.add_argument(
        "--taste-skill",
        help="Override the mode default; use 'none' to skip Taste Skill.",
    )
    parser.add_argument("--skills-version", default=SKILLS_CLI_VERSION)
    parser.add_argument("--impeccable-version", default=IMPECCABLE_VERSION)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Execute the planned installation commands. Default is plan-only.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        plan = build_plan(args)
        if args.apply:
            project = Path(str(plan["project"]))
            plan["execution"] = []
            for item in plan["commands"]:
                plan["execution"].append(run(list(item["command"]), project))
            selected = [state["skill"] for state in plan["states_before"]]
            plan["states_after"] = [
                skill_state(project, str(skill)) for skill in selected
            ]
            incomplete = [
                state["skill"]
                for state in plan["states_after"]
                if not state["complete"]
            ]
            if incomplete:
                raise RuntimeError(
                    "Installation verification failed for: "
                    + ", ".join(str(name) for name in incomplete)
                )
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        payload = {"ok": False, "error": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    payload = {"ok": True, **plan}
    if args.json:
        serializable = {
            **payload,
            "commands": [
                {key: value for key, value in item.items() if key != "command"}
                for item in payload["commands"]
            ],
        }
        print(json.dumps(serializable, ensure_ascii=False, indent=2))
    else:
        print(f"Project: {plan['project']}")
        print(f"Mode: {plan['mode']}")
        print(f"Taste Skill: {plan['taste_skill'] or 'none'}")
        if plan["commands"]:
            for item in plan["commands"]:
                print(f"- {item['display']}")
        else:
            print("No installation commands are needed.")
        if not args.apply:
            print("Plan only. Re-run with --apply to install.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
