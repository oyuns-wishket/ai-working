#!/usr/bin/env python3
"""Commit and push only user-approved files from a connected wiki repository."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set


class PublishError(RuntimeError):
    """Raised when a safe automatic publish cannot proceed."""


def _redact(text: str) -> str:
    redacted = re.sub(
        r"([a-z][a-z0-9+.-]*://)[^/@\s]+@",
        r"\1***@",
        text,
        flags=re.I,
    )
    return re.sub(
        r"([a-z][a-z0-9+.-]*://[^ \t\r\n?#]+)([?#])[^ \t\r\n]+",
        r"\1\2***",
        redacted,
        flags=re.I,
    )


def _result_detail(result: subprocess.CompletedProcess) -> str:
    parts = [part.strip() for part in (result.stderr, result.stdout) if part.strip()]
    return _redact("\n".join(parts))


def _git(
    repo: Path,
    args: Sequence[str],
    *,
    check: bool = True,
    env_extra: Optional[Dict[str, str]] = None,
    input_text: Optional[str] = None,
) -> subprocess.CompletedProcess:
    environment = {
        **os.environ,
        "GIT_TERMINAL_PROMPT": "0",
        "GCM_INTERACTIVE": "Never",
    }
    if env_extra:
        environment.update(env_extra)
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
        check=False,
    )
    if check and result.returncode != 0:
        detail = _result_detail(result)
        raise PublishError(detail or "git command failed")
    return result


def _resolve_repo(value: str) -> Path:
    repo = Path(value).expanduser().resolve()
    if not repo.is_dir():
        raise PublishError(f"wiki repository does not exist: {repo}")
    root = Path(_git(repo, ["rev-parse", "--show-toplevel"]).stdout.strip()).resolve()
    if root != repo:
        raise PublishError(f"--repo must be the wiki Git root: {root}")
    return repo


def _resolve_project_repo(value: str) -> Path:
    project = Path(value).expanduser().resolve()
    if not project.is_dir():
        raise PublishError(f"project repository does not exist: {project}")
    result = _git(project, ["rev-parse", "--show-toplevel"], check=False)
    if result.returncode != 0:
        raise PublishError("project root must belong to a Git repository")
    return Path(result.stdout.strip()).resolve()


def _git_common_dir(repo: Path) -> Path:
    value = _git(repo, ["rev-parse", "--git-common-dir"]).stdout.strip()
    common = Path(value)
    if not common.is_absolute():
        common = repo / common
    return common.resolve()


def _resolve_paths(repo: Path, values: Sequence[str]) -> List[str]:
    approved: List[str] = []
    seen: Set[str] = set()
    for value in values:
        candidate = Path(value).expanduser()
        absolute = Path(
            os.path.abspath(str(candidate if candidate.is_absolute() else repo / candidate))
        )
        try:
            relative = absolute.relative_to(repo)
        except ValueError as exc:
            raise PublishError(f"approved path is outside the wiki repository: {value}") from exc
        if relative == Path("."):
            raise PublishError("repository root cannot be an approved path")
        cursor = repo
        for part in relative.parts:
            cursor = cursor / part
            if cursor.is_symlink():
                raise PublishError(f"approved paths cannot traverse symlinks: {relative}")
        if absolute.exists() and absolute.is_dir():
            raise PublishError(f"approved paths must name files, not directories: {relative}")
        normalized = relative.as_posix()
        if normalized not in seen:
            approved.append(normalized)
            seen.add(normalized)
    if not approved:
        raise PublishError("at least one approved file path is required")
    return approved


def _current_branch(repo: Path) -> str:
    result = _git(repo, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    branch = result.stdout.strip()
    if result.returncode != 0 or not branch:
        raise PublishError("detached HEAD is not eligible for automatic publish")
    return branch


def _ensure_clean_index(repo: Path) -> None:
    result = _git(repo, ["diff", "--cached", "--quiet", "--exit-code"], check=False)
    if result.returncode == 1:
        raise PublishError("index already has staged changes; automatic publish would be ambiguous")
    if result.returncode != 0:
        raise PublishError(_redact(result.stderr.strip()) or "could not inspect staged changes")


def _ensure_changes(repo: Path, paths: Sequence[str]) -> None:
    result = _git(
        repo,
        [
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--",
            *(_literal_pathspec(path) for path in paths),
        ],
    )
    if not result.stdout:
        raise PublishError("none of the approved files has a change to publish")


def _remote_identity(repo: Path, remote: str, expected_url: str) -> str:
    remotes = set(_git(repo, ["remote"]).stdout.splitlines())
    if remote not in remotes:
        raise PublishError(f"configured remote does not exist: {remote}")

    fetch_urls = [
        _redact(line)
        for line in _git(repo, ["remote", "get-url", "--all", remote]).stdout.splitlines()
        if line.strip()
    ]
    push_urls = [
        _redact(line)
        for line in _git(
            repo,
            ["remote", "get-url", "--push", "--all", remote],
        ).stdout.splitlines()
        if line.strip()
    ]
    if len(fetch_urls) != 1 or len(push_urls) != 1:
        raise PublishError("remote must have exactly one fetch URL and one push URL")
    if fetch_urls[0] != push_urls[0]:
        raise PublishError("remote fetch URL and push URL differ; automatic publish was blocked")
    if fetch_urls[0] != expected_url:
        raise PublishError("configured remote URL does not match the approved redacted URL")
    return fetch_urls[0]


def _remote_tip(repo: Path, remote: str, branch: str) -> Optional[str]:
    result = _git(
        repo,
        ["ls-remote", "--heads", remote, f"refs/heads/{branch}"],
        check=False,
    )
    if result.returncode != 0:
        detail = _result_detail(result)
        raise PublishError(detail or "could not read the remote branch")
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return None
    if len(lines) != 1:
        raise PublishError("remote branch lookup returned an ambiguous result")
    return lines[0].split()[0]


def _remote_contains_commit(repo: Path, remote: str, commit_sha: str) -> bool:
    result = _git(repo, ["ls-remote", remote], check=False)
    if result.returncode != 0:
        detail = _result_detail(result)
        raise PublishError(detail or "could not inspect remote refs")
    advertised = {
        line.split()[0]
        for line in result.stdout.splitlines()
        if line.strip() and len(line.split()) >= 2
    }
    return commit_sha in advertised


def _ensure_identity(repo: Path) -> None:
    _git(repo, ["var", "GIT_AUTHOR_IDENT"])
    _git(repo, ["var", "GIT_COMMITTER_IDENT"])


def _ensure_no_active_publish_hooks(repo: Path) -> None:
    for hook_name in (
        "pre-commit",
        "prepare-commit-msg",
        "commit-msg",
        "post-commit",
        "pre-push",
    ):
        value = _git(repo, ["rev-parse", "--git-path", f"hooks/{hook_name}"]).stdout.strip()
        hook = Path(value)
        if not hook.is_absolute():
            hook = repo / hook
        if hook.is_file() and os.access(str(hook), os.X_OK):
            raise PublishError(
                f"active Git hook {hook_name!r} makes automatic publish scope non-deterministic"
            )


def _ensure_supported_commit_policy(repo: Path) -> None:
    result = _git(repo, ["config", "--bool", "commit.gpgSign"], check=False)
    if result.returncode == 0 and result.stdout.strip() == "true":
        raise PublishError(
            "automatic publisher does not bypass or emulate required signed commits"
        )


def _staged_paths(
    repo: Path,
    *,
    env_extra: Optional[Dict[str, str]] = None,
) -> Set[str]:
    result = _git(
        repo,
        ["diff", "--cached", "--name-only", "--no-renames", "-z"],
        env_extra=env_extra,
    )
    return {path for path in result.stdout.split("\0") if path}


def _literal_pathspec(path: str) -> str:
    return f":(literal){path}"


def _worktree_states(repo: Path, paths: Sequence[str]) -> Dict[str, str]:
    states: Dict[str, str] = {}
    for path in paths:
        absolute = repo / path
        if not absolute.exists():
            states[path] = "DELETED"
            continue
        if not absolute.is_file() or absolute.is_symlink():
            raise PublishError(f"approved path is not a regular file: {path}")
        mode = "100755" if absolute.stat().st_mode & 0o111 else "100644"
        blob = _git(repo, ["hash-object", "--path", path, "--", path]).stdout.strip()
        states[path] = f"{mode}:{blob}"
    return states


def _commit_states(
    repo: Path,
    paths: Sequence[str],
    commit: str = "HEAD",
) -> Dict[str, str]:
    states: Dict[str, str] = {}
    for path in paths:
        result = _git(
            repo,
            ["ls-tree", "-z", commit, "--", _literal_pathspec(path)],
        ).stdout
        entries = [entry for entry in result.split("\0") if entry]
        if not entries:
            states[path] = "DELETED"
            continue
        if len(entries) != 1:
            raise PublishError(f"commit tree lookup was ambiguous for approved path: {path}")
        metadata, actual_path = entries[0].split("\t", 1)
        mode, object_type, object_sha = metadata.split()
        if actual_path != path or object_type != "blob":
            raise PublishError(f"commit tree contains a non-file approved path: {path}")
        states[path] = f"{mode}:{object_sha}"
    return states


def _index_states(
    repo: Path,
    paths: Sequence[str],
    *,
    env_extra: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    states: Dict[str, str] = {}
    for path in paths:
        result = _git(
            repo,
            ["ls-files", "--stage", "-z", "--", _literal_pathspec(path)],
            env_extra=env_extra,
        ).stdout
        entries = [entry for entry in result.split("\0") if entry]
        if not entries:
            states[path] = "DELETED"
            continue
        if len(entries) != 1:
            raise PublishError(f"index lookup was ambiguous for approved path: {path}")
        metadata, actual_path = entries[0].split("\t", 1)
        mode, object_sha, stage = metadata.split()
        if actual_path != path or stage != "0":
            raise PublishError(f"index contains a conflicted approved path: {path}")
        states[path] = f"{mode}:{object_sha}"
    return states


def _preflight_token(
    *,
    repo: Path,
    project_repo: Path,
    paths: Sequence[str],
    states: Dict[str, str],
    head: str,
    branch: str,
    remote: str,
    remote_url: str,
    message: str,
    allow_new_branch: bool,
    new_branch_base: Optional[str],
) -> str:
    values = [
        str(repo),
        str(_git_common_dir(repo)),
        str(project_repo),
        str(_git_common_dir(project_repo)),
        head,
        branch,
        remote,
        remote_url,
        message,
        "allow-new-branch" if allow_new_branch else "existing-branch",
        new_branch_base or "",
    ]
    values.extend(f"{path}:{states[path]}" for path in sorted(paths))
    return hashlib.sha256("\0".join(values).encode("utf-8")).hexdigest()


def publish(
    *,
    repo_value: str,
    project_repo_value: str,
    path_values: Sequence[str],
    message: str,
    remote: str,
    expected_remote_url: str,
    expected_branch: str,
    allow_new_branch: bool,
    new_branch_base: Optional[str],
    preflight_token: Optional[str],
    dry_run: bool,
) -> str:
    repo = _resolve_repo(repo_value)
    project_repo = _resolve_project_repo(project_repo_value)
    if repo == project_repo or _git_common_dir(repo) == _git_common_dir(project_repo):
        raise PublishError("connected wiki Git root is the project code repository")
    paths = _resolve_paths(repo, path_values)
    branch = _current_branch(repo)
    if branch != expected_branch:
        raise PublishError(
            f"current branch {branch!r} does not match approved branch {expected_branch!r}"
        )
    if (
        not message.strip()
        or message != message.strip()
        or "\n" in message
        or "\0" in message
    ):
        raise PublishError("commit message must be a trimmed, non-empty single line")

    _ensure_clean_index(repo)
    _ensure_changes(repo, paths)
    _ensure_identity(repo)
    _ensure_no_active_publish_hooks(repo)
    _ensure_supported_commit_policy(repo)

    head_before = _git(repo, ["rev-parse", "HEAD"]).stdout.strip()
    remote_url = _remote_identity(repo, remote, expected_remote_url)
    remote_tip = _remote_tip(repo, remote, branch)
    if remote_tip is None and not allow_new_branch:
        raise PublishError(
            "approved remote branch does not exist; explicit --allow-new-branch is required"
        )
    if remote_tip is None:
        if not new_branch_base:
            raise PublishError("approved new branch requires an exact --new-branch-base SHA")
        if not re.fullmatch(r"[0-9a-fA-F]{40,64}", new_branch_base):
            raise PublishError("--new-branch-base must be a full commit SHA")
        if new_branch_base.lower() != head_before.lower():
            raise PublishError("current HEAD does not match the approved new branch base SHA")
        if not _remote_contains_commit(repo, remote, new_branch_base):
            raise PublishError(
                "new remote branch base is not advertised by the approved remote"
            )
    elif allow_new_branch or new_branch_base:
        raise PublishError("new-branch approval was supplied but the remote branch already exists")
    if remote_tip is not None and remote_tip != head_before:
        raise PublishError(
            "remote branch tip does not match local HEAD; pull/reconcile before publishing"
        )

    states_before = _worktree_states(repo, paths)
    computed_token = _preflight_token(
        repo=repo,
        project_repo=project_repo,
        paths=paths,
        states=states_before,
        head=head_before,
        branch=branch,
        remote=remote,
        remote_url=remote_url,
        message=message,
        allow_new_branch=allow_new_branch,
        new_branch_base=new_branch_base,
    )
    if dry_run:
        if preflight_token:
            raise PublishError("--preflight-token is not accepted with --dry-run")
        return (
            f"READY: {repo}\n"
            f"BRANCH: {branch}\n"
            f"REMOTE: {remote}\n"
            f"REMOTE_URL: {remote_url}\n"
            f"FILES: {', '.join(paths)}\n"
            f"NEW_BRANCH: {'yes' if remote_tip is None else 'no'}\n"
            f"NEW_BRANCH_BASE: {new_branch_base or 'not-applicable'}\n"
            f"PREFLIGHT_TOKEN: {computed_token}"
        )
    if not preflight_token:
        raise PublishError("actual publish requires the token from a successful --dry-run")
    if preflight_token != computed_token:
        raise PublishError("approved files or Git publish state changed after preflight")

    literal_paths = [_literal_pathspec(path) for path in paths]
    approved = set(paths)
    with tempfile.TemporaryDirectory(prefix="knowns-publish-index-") as temporary:
        index_env = {"GIT_INDEX_FILE": str(Path(temporary) / "index")}
        _git(repo, ["read-tree", head_before], env_extra=index_env)
        _git(
            repo,
            ["add", "--all", "--", *literal_paths],
            env_extra=index_env,
        )
        staged = _staged_paths(repo, env_extra=index_env)
        if not staged:
            raise PublishError("approved files produced no staged diff")
        unexpected = staged - approved
        if unexpected:
            raise PublishError(
                "temporary staging included files outside the approved plan: "
                + ", ".join(sorted(unexpected))
            )
        if _index_states(repo, paths, env_extra=index_env) != states_before:
            raise PublishError(
                "approved file content changed between preflight validation and staging"
            )
        tree_sha = _git(repo, ["write-tree"], env_extra=index_env).stdout.strip()

    commit_sha = _git(
        repo,
        ["commit-tree", tree_sha, "-p", head_before],
        input_text=f"{message}\n",
    ).stdout.strip()
    committed = {
        path
        for path in _git(
            repo,
            [
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "--no-renames",
                "-r",
                "-z",
                commit_sha,
            ],
        ).stdout.split("\0")
        if path
    }
    unexpected_commit = committed - approved
    if unexpected_commit:
        raise PublishError(
            "local commit contains files outside the approved plan; push was blocked: "
            + ", ".join(sorted(unexpected_commit))
        )
    if _commit_states(repo, paths, commit_sha) != states_before:
        raise PublishError(
            f"candidate commit {commit_sha} content differs from the approved preflight"
        )
    committed_message = _git(
        repo,
        ["show", "-s", "--format=%B", commit_sha],
    ).stdout.strip()
    if committed_message != message:
        raise PublishError(
            f"candidate commit {commit_sha} message differs from the approved plan"
        )

    _remote_identity(repo, remote, expected_remote_url)
    remote_tip_before_push = _remote_tip(repo, remote, branch)
    if remote_tip_before_push != remote_tip:
        raise PublishError(
            f"remote branch changed after preflight; candidate commit {commit_sha} was not pushed"
        )
    _git(
        repo,
        ["update-ref", f"refs/heads/{branch}", commit_sha, head_before],
    )
    _git(
        repo,
        ["restore", "--staged", "--source=HEAD", "--", *literal_paths],
    )
    remaining_staged = _staged_paths(repo)
    if remaining_staged:
        raise PublishError(
            f"index changed concurrently after local commit {commit_sha}; push was blocked: "
            + ", ".join(sorted(remaining_staged))
        )
    try:
        _git(
            repo,
            ["push", "--porcelain", "--atomic", remote, f"HEAD:refs/heads/{branch}"],
        )
    except PublishError as exc:
        raise PublishError(f"push failed after local commit {commit_sha}: {exc}") from exc
    return (
        f"PUBLISHED: {commit_sha}\n"
        f"BRANCH: {branch}\n"
        f"REMOTE: {remote}\n"
        f"REMOTE_URL: {remote_url}\n"
        f"FILES: {', '.join(sorted(committed))}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely commit and push only approved files in a connected wiki repository."
    )
    parser.add_argument("--repo", required=True, help="Connected wiki Git repository root")
    parser.add_argument(
        "--project-repo",
        required=True,
        help="Project Git repository path; it must not resolve to the wiki Git root",
    )
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        required=True,
        help="Exact approved file path; repeat for every file",
    )
    parser.add_argument("--message", required=True, help="Approved one-line commit message")
    parser.add_argument("--remote", required=True, help="Approved Git remote name")
    parser.add_argument(
        "--remote-url",
        required=True,
        help="Approved redacted fetch/push URL; credential userinfo must be written as ***",
    )
    parser.add_argument("--branch", required=True, help="Approved current branch")
    parser.add_argument(
        "--allow-new-branch",
        action="store_true",
        help="Allow creating the approved branch when it does not exist on the remote",
    )
    parser.add_argument(
        "--new-branch-base",
        help="Approved full remote-advertised base SHA for a new remote branch",
    )
    parser.add_argument(
        "--preflight-token",
        help="Token emitted by --dry-run; required for the actual publish",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run all read-only safety checks without staging, committing, or pushing",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = publish(
            repo_value=args.repo,
            project_repo_value=args.project_repo,
            path_values=args.paths,
            message=args.message,
            remote=args.remote,
            expected_remote_url=args.remote_url,
            expected_branch=args.branch,
            allow_new_branch=args.allow_new_branch,
            new_branch_base=args.new_branch_base,
            preflight_token=args.preflight_token,
            dry_run=args.dry_run,
        )
    except PublishError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
