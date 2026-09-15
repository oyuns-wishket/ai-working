#!/usr/bin/env python3
"""Merge completed lane branches into the Lead task branch, one at a time.

Order: plan order. Each lane is checked with `git merge-tree` first; a lane
with conflicts is reported and skipped, never auto-resolved. After merging,
the given verification commands run in the integration workspace.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any

from session_runner import default_state_root, load_task_state, save_task_state, task_dir
from worktree_manager import dirty_paths, git_root, run_git

VERIFY_TAIL_LINES = 40


def current_branch(repo: Path) -> str:
    return run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()


def head_sha(repo: Path, ref: str = "HEAD") -> str:
    return run_git(repo, ["rev-parse", ref]).stdout.strip()


def is_ancestor(repo: Path, branch: str, target: str) -> bool:
    return (
        run_git(repo, ["merge-base", "--is-ancestor", branch, target], check=False).returncode
        == 0
    )


def merge_tree_conflicts(repo: Path, target: str, branch: str) -> tuple[bool, list[str], str]:
    """Return (clean, conflicted_files, raw_output) using git merge-tree --write-tree."""
    result = run_git(
        repo,
        ["merge-tree", "--write-tree", "--name-only", target, branch],
        check=False,
    )
    if result.returncode == 0:
        return True, [], result.stdout
    if result.returncode == 1:
        lines = result.stdout.splitlines()
        files = [line for line in lines[1:] if line.strip()]
        return False, files, result.stdout
    raise RuntimeError(f"git merge-tree failed: {result.stderr.strip()}")


def run_verify(repo: Path, command: str, log_path: Path) -> dict[str, Any]:
    started = time.time()
    result = subprocess.run(
        command,
        shell=True,
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(output, encoding="utf-8")
    tail = output.strip().splitlines()[-VERIFY_TAIL_LINES:]
    return {
        "command": command,
        "exit_code": result.returncode,
        "seconds": round(time.time() - started, 1),
        "log": str(log_path),
        "tail": tail,
    }


def command_integrate(args: argparse.Namespace) -> int:
    repo = git_root(Path(args.repo).expanduser())
    state_root = Path(args.state_root).expanduser()
    state = load_task_state(state_root, repo, args.task)
    if not state.get("lanes"):
        raise SystemExit(f"no lane state for task {args.task}; run session_runner.py first")
    target = args.target or state.get("target_branch")
    if not target:
        raise SystemExit("target branch unknown; pass --target")

    branch_now = current_branch(repo)
    if branch_now != target:
        raise SystemExit(
            f"repo is on '{branch_now}', expected target '{target}'; check out the target first"
        )
    dirty = dirty_paths(repo)
    if dirty:
        raise SystemExit(f"integration workspace is dirty: {', '.join(dirty)}")

    plan_order = state.get("lane_order") or list(state["lanes"].keys())
    selected = args.lane or [
        lane_id
        for lane_id in plan_order
        if state["lanes"].get(lane_id, {}).get("branch")
        and state["lanes"].get(lane_id, {}).get("status") == "complete"
    ]

    merged: list[dict[str, Any]] = []
    conflicted: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for lane_id in selected:
        lane = state["lanes"].get(lane_id)
        if not lane or not lane.get("branch"):
            skipped.append({"lane": lane_id, "reason": "no-branch"})
            continue
        branch = lane["branch"]
        if lane.get("status") != "complete" and not args.lane:
            skipped.append({"lane": lane_id, "reason": f"status-{lane.get('status')}"})
            continue
        if is_ancestor(repo, branch, "HEAD"):
            skipped.append({"lane": lane_id, "branch": branch, "reason": "already-integrated"})
            continue
        clean, files, _ = merge_tree_conflicts(repo, "HEAD", branch)
        if not clean:
            conflicted.append({"lane": lane_id, "branch": branch, "files": files})
            continue
        if args.dry_run:
            merged.append({"lane": lane_id, "branch": branch, "dry_run": True})
            continue
        merge = run_git(
            repo,
            ["merge", "--no-ff", "--no-edit", "-m", f"merge(msd): lane {lane_id}", branch],
            check=False,
        )
        if merge.returncode != 0:
            run_git(repo, ["merge", "--abort"], check=False)
            conflicted.append(
                {"lane": lane_id, "branch": branch, "files": [], "detail": merge.stderr.strip()}
            )
            continue
        merged.append({"lane": lane_id, "branch": branch, "merge_sha": head_sha(repo)})

    verify: list[dict[str, Any]] = []
    if not args.dry_run and not conflicted:
        log_dir = task_dir(state_root, repo, args.task) / "integrate"
        for index, command in enumerate(args.verify or []):
            verify.append(run_verify(repo, command, log_dir / f"verify-{index}.log"))

    ok = not conflicted and all(item["exit_code"] == 0 for item in verify)
    payload = {
        "task": args.task,
        "repo": str(repo),
        "target": target,
        "head": head_sha(repo),
        "dry_run": args.dry_run,
        "merged": merged,
        "conflicted": conflicted,
        "skipped": skipped,
        "verify": verify,
        "ok": ok,
    }
    if not args.dry_run:
        state["integration"] = {
            key: payload[key] for key in ("target", "head", "merged", "conflicted", "skipped", "verify", "ok")
        }
        state["integration"]["at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        save_task_state(state_root, repo, args.task, state)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sequentially merge lane branches into the target branch.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--target", help="Target branch; defaults to the plan's target_branch")
    parser.add_argument("--lane", action="append", help="Explicit lane ids (default: all complete lanes)")
    parser.add_argument("--verify", action="append", help="Shell command to run after merging (repeatable)")
    parser.add_argument("--dry-run", action="store_true", help="Only run merge-tree conflict checks")
    parser.add_argument("--state-root", default=str(default_state_root()))
    parser.add_argument("--json", action="store_true")
    parser.set_defaults(func=command_integrate)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
