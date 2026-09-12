#!/usr/bin/env python3
"""Create and safely clean isolated Git worktrees for write workers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from configure import default_config_path, load_config

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GENERATED_WORKER_PREFIXES = (
    ".agents/multi-agent-dev/workers/",
    ".claude/agents/",
    ".codex/agents/",
)


def run_git(
    repo: Path, args: list[str], *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed in {repo}: {result.stderr.strip()}"
        )
    return result


def git_root(project: Path) -> Path:
    result = run_git(project, ["rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip()).resolve()


def default_state_root() -> Path:
    root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return root / "multi-agent-dev"


def repo_id(repo: Path) -> str:
    digest = hashlib.sha256(str(repo).encode()).hexdigest()[:12]
    return f"{repo.name}-{digest}"


def state_path(repo: Path, session: str, state_root: Path) -> Path:
    return state_root / "sessions" / repo_id(repo) / f"{session}.json"


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "workers": {}}
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def validate_slug(value: str, label: str) -> None:
    if not SLUG_PATTERN.fullmatch(value):
        raise SystemExit(f"{label} must be lowercase kebab-case: {value}")


def dirty_paths(repo: Path) -> list[str]:
    result = run_git(
        repo,
        ["status", "--porcelain=v1", "--untracked-files=all", "-z"],
    )
    entries = [entry for entry in result.stdout.split("\0") if entry]
    paths: list[str] = []
    for entry in entries:
        value = entry[3:] if len(entry) > 3 else entry
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        paths.append(value)
    return paths


def only_generated_worker_metadata(paths: list[str]) -> bool:
    return bool(paths) and all(
        any(path.startswith(prefix) for prefix in GENERATED_WORKER_PREFIXES)
        for path in paths
    )


def resolve_worktree_root(args: argparse.Namespace) -> Path:
    if args.worktree_root:
        return Path(args.worktree_root).expanduser().resolve(strict=False)
    config = load_config(Path(args.config).expanduser())
    value = config.get("worktree_root")
    if not value:
        raise SystemExit("worktree_root is not configured; run configure.py set first")
    return Path(value).expanduser().resolve(strict=False)


def command_create(args: argparse.Namespace) -> int:
    validate_slug(args.session, "session")
    validate_slug(args.worker, "worker")
    repo = git_root(Path(args.repo).expanduser())
    dirty = dirty_paths(repo)
    metadata_exception = (
        args.allow_generated_worker_metadata and only_generated_worker_metadata(dirty)
    )
    if dirty and not metadata_exception:
        raise SystemExit(
            "Lead workspace is dirty; refusing to create a worker worktree. "
            f"Dirty paths: {', '.join(dirty)}"
        )

    root = resolve_worktree_root(args)
    worker_path = root / repo.name / args.session / args.worker
    branch = f"mad/{args.session}/{args.worker}"
    if worker_path.exists():
        raise SystemExit(f"Worker path already exists: {worker_path}")
    if (
        run_git(
            repo,
            ["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
            check=False,
        ).returncode
        == 0
    ):
        raise SystemExit(f"Worker branch already exists: {branch}")

    worker_path.parent.mkdir(parents=True, exist_ok=True)
    run_git(
        repo,
        ["worktree", "add", "-b", branch, str(worker_path), args.base_ref],
    )

    state_root = Path(args.state_root).expanduser()
    manifest_path = state_path(repo, args.session, state_root)
    state = load_state(manifest_path)
    state.update(
        {
            "schema_version": 1,
            "repo": str(repo),
            "session": args.session,
            "target_ref_at_creation": args.base_ref,
        }
    )
    state.setdefault("workers", {})[args.worker] = {
        "path": str(worker_path),
        "branch": branch,
        "base_ref": args.base_ref,
    }
    atomic_write(manifest_path, state)
    payload = {
        "created": True,
        "repo": str(repo),
        "session": args.session,
        "worker": args.worker,
        "worktree_path": str(worker_path),
        "branch": branch,
        "manifest": str(manifest_path),
        "excluded_dirty_worker_metadata": dirty if metadata_exception else [],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_status(args: argparse.Namespace) -> int:
    validate_slug(args.session, "session")
    repo = git_root(Path(args.repo).expanduser())
    manifest_path = state_path(repo, args.session, Path(args.state_root).expanduser())
    state = load_state(manifest_path)
    workers = []
    for name, worker in state.get("workers", {}).items():
        path = Path(worker["path"])
        workers.append(
            {
                "worker": name,
                **worker,
                "path_exists": path.is_dir(),
                "dirty_paths": dirty_paths(path) if path.is_dir() else [],
            }
        )
    print(
        json.dumps(
            {
                "repo": str(repo),
                "session": args.session,
                "manifest": str(manifest_path),
                "workers": workers,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def integrated(repo: Path, branch: str, target_ref: str) -> bool:
    return (
        run_git(
            repo,
            ["merge-base", "--is-ancestor", branch, target_ref],
            check=False,
        ).returncode
        == 0
    )


def command_cleanup(args: argparse.Namespace) -> int:
    validate_slug(args.session, "session")
    repo = git_root(Path(args.repo).expanduser())
    state_root = Path(args.state_root).expanduser()
    manifest_path = state_path(repo, args.session, state_root)
    state = load_state(manifest_path)
    removed: list[dict[str, str]] = []
    preserved: list[dict[str, Any]] = []

    for name, worker in list(state.get("workers", {}).items()):
        path = Path(worker["path"])
        branch = worker["branch"]
        if not path.is_dir():
            preserved.append(
                {"worker": name, "path": str(path), "reason": "path-missing"}
            )
            continue
        dirty = dirty_paths(path)
        if dirty:
            preserved.append(
                {
                    "worker": name,
                    "path": str(path),
                    "branch": branch,
                    "reason": "dirty",
                    "dirty_paths": dirty,
                }
            )
            continue
        if not integrated(repo, branch, args.target_ref):
            preserved.append(
                {
                    "worker": name,
                    "path": str(path),
                    "branch": branch,
                    "reason": "not-integrated",
                }
            )
            continue
        run_git(repo, ["worktree", "remove", str(path)])
        deletion = run_git(repo, ["branch", "-d", branch], check=False)
        if deletion.returncode != 0:
            preserved.append(
                {
                    "worker": name,
                    "path": str(path),
                    "branch": branch,
                    "reason": "worktree-removed-branch-preserved",
                    "detail": deletion.stderr.strip(),
                }
            )
        else:
            removed.append({"worker": name, "path": str(path), "branch": branch})
        del state["workers"][name]

    run_git(repo, ["worktree", "prune"])
    if state.get("workers"):
        atomic_write(manifest_path, state)
    elif manifest_path.exists():
        manifest_path.unlink()
        parent = manifest_path.parent
        if parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()

    print(
        json.dumps(
            {
                "repo": str(repo),
                "session": args.session,
                "target_ref": args.target_ref,
                "removed": removed,
                "preserved": preserved,
                "manifest": str(manifest_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage isolated Git worktrees for write workers."
    )
    parser.add_argument("--config", default=str(default_config_path()))
    parser.add_argument("--state-root", default=str(default_state_root()))
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--repo", required=True)
    create.add_argument("--session", required=True)
    create.add_argument("--worker", required=True)
    create.add_argument("--base-ref", default="HEAD")
    create.add_argument("--worktree-root")
    create.add_argument("--allow-generated-worker-metadata", action="store_true")
    create.add_argument("--json", action="store_true")
    create.set_defaults(func=command_create)

    status = subparsers.add_parser("status")
    status.add_argument("--repo", required=True)
    status.add_argument("--session", required=True)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_status)

    cleanup = subparsers.add_parser("cleanup")
    cleanup.add_argument("--repo", required=True)
    cleanup.add_argument("--session", required=True)
    cleanup.add_argument("--target-ref", required=True)
    cleanup.add_argument("--json", action="store_true")
    cleanup.set_defaults(func=command_cleanup)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except RuntimeError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    raise SystemExit(main())
