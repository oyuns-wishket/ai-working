#!/usr/bin/env python3
"""Fail closed when a public ai-working commit contains private-only material."""

from __future__ import annotations

import argparse
import base64
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_LIMIT = 1_000_000
LEGACY_WAIVERS = {
    "bootstrap.sh",
    "docs/impl-notes/2026-09-12-public-only-ssot.md",
    "docs/migration-ledger.md",
    "tests/bootstrap.test.mjs",
}


def run(*args: str) -> bytes:
    return subprocess.check_output(args, cwd=ROOT)


def tracked() -> list[tuple[str, str]]:
    records = run("git", "ls-files", "-s", "-z").decode().split("\0")
    result: list[tuple[str, str]] = []
    for record in records:
        if not record:
            continue
        metadata, path = record.split("\t", 1)
        result.append((metadata.split()[0], path))
    return result


def patterns() -> dict[str, re.Pattern[bytes]]:
    legacy_name = "|".join(
        ["wishket" + "-working", "ai-working" + "-private", "claude-skills" + "-kit", "private " + "overlay"]
    )
    result = {
        "credential": re.compile(
            rb"x(?:ox[baprs]|app)-[A-Za-z0-9-]{10,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|"
            rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{35}|"
            rb"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b|"
            rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|https?://[^\s/:]+:[^\s/@]+@"
        ),
        "private_network": re.compile(
            rb"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}|100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])(?:\.\d{1,3}){2})\b|[A-Za-z0-9.-]+\.ts\.net\b"
        ),
        "local_hostname": re.compile(
            rb"(?<![A-Za-z0-9.-])[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.local(?=$|[/:\s'\"),])",
            re.IGNORECASE,
        ),
        "personal_home": re.compile(
            (re.escape("/Users/") + r"(?!(?:you|username|example|yourname)(?:/|\b))[A-Za-z0-9._-]+").encode(),
            re.IGNORECASE,
        ),
        "slack_identifier": re.compile(
            rb"<@[UW](?=[A-Z0-9]{8,}>)(?=[A-Z0-9]*\d)[A-Z0-9]+>|"
            rb"\bC(?=[A-Z0-9]{8,}\b)(?=[A-Z0-9]*\d)[A-Z0-9]{8,}\b"
        ),
        "legacy_name": re.compile(legacy_name.encode(), re.IGNORECASE),
    }
    denylist: list[bytes] = []
    denylist_paths = [Path.home() / ".config" / "ai-working" / "public-audit-denylist.txt"]
    if os.environ.get("AI_WORKING_AUDIT_DENYLIST_FILE"):
        denylist_paths.append(Path(os.environ["AI_WORKING_AUDIT_DENYLIST_FILE"]).expanduser())
    for denylist_path in denylist_paths:
        if denylist_path.is_file():
            denylist.extend(denylist_path.read_bytes().splitlines())
    encoded = os.environ.get("AI_WORKING_AUDIT_DENYLIST_B64")
    if encoded:
        denylist.extend(base64.b64decode(encoded, validate=True).splitlines())
    denylist = [item.strip() for item in denylist if item.strip() and not item.lstrip().startswith(b"#")]
    if denylist:
        result["local_denylist"] = re.compile(b"|".join(re.escape(item) for item in denylist), re.IGNORECASE)
    return result


def forbidden_path(path: str) -> str | None:
    pieces = Path(path).parts
    if pieces and pieces[0] in {"memory", ".omc", "private"}:
        return "private-only directory"
    if any(piece in {"__pycache__", ".ruff_cache", ".pytest_cache"} for piece in pieces):
        return "cache directory"
    name = Path(path).name.lower()
    if name == ".env" or name.startswith(".env.") or name.endswith((".pem", ".key", ".p12", ".pyc")):
        return "credential/cache filename"
    if any(word in name for word in ("credential", "oauth-token", "private-key")):
        return "sensitive filename"
    return None


def scan_blob(path: str, data: bytes, checks: dict[str, re.Pattern[bytes]], *, history: bool) -> list[str]:
    failures: list[str] = []
    if len(data) > TEXT_LIMIT:
        failures.append("oversize")
        return failures
    if b"\0" in data:
        failures.append("binary")
        return failures
    for category, pattern in checks.items():
        if category == "legacy_name" and path in LEGACY_WAIVERS:
            continue
        if pattern.search(data):
            failures.append(category)
    return failures


def history_blobs() -> list[tuple[str, str, bytes]]:
    result: list[tuple[str, str, bytes]] = []
    seen: set[str] = set()
    for line in run("git", "rev-list", "--objects", "--all").decode(errors="replace").splitlines():
        oid, _, path = line.partition(" ")
        if not path or oid in seen:
            continue
        seen.add(oid)
        if run("git", "cat-file", "-t", oid).strip() != b"blob":
            continue
        result.append((oid, path, run("git", "cat-file", "blob", oid)))
    return result


def history_tree_entries() -> list[tuple[str, str, str]]:
    result: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for commit in run("git", "rev-list", "--all").decode().splitlines():
        records = run("git", "ls-tree", "-rz", "-r", commit).split(b"\0")
        for record in records:
            if not record:
                continue
            metadata, raw_path = record.split(b"\t", 1)
            mode, kind, _oid = metadata.decode().split()
            path = raw_path.decode(errors="replace")
            key = (mode, kind, path)
            if key not in seen:
                seen.add(key)
                result.append(key)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", action="store_true", help="also scan every reachable Git blob")
    args = parser.parse_args()
    checks = patterns()
    failures: list[str] = []

    for mode, path in tracked():
        reason = forbidden_path(path)
        if reason:
            failures.append(f"tree:{path}:{reason}")
            continue
        if mode != "100644" and mode != "100755":
            failures.append(f"tree:{path}:unsupported-mode-{mode}")
            continue
        data = (ROOT / path).read_bytes()
        failures.extend(f"tree:{path}:{category}" for category in scan_blob(path, data, checks, history=False))

    if args.history:
        for mode, kind, path in history_tree_entries():
            reason = forbidden_path(path)
            if reason:
                failures.append(f"history-tree:{path}:{reason}")
            if kind != "blob" or mode not in {"100644", "100755"}:
                failures.append(f"history-tree:{path}:unsupported-{kind}-{mode}")
        for oid, path, data in history_blobs():
            failures.extend(
                f"history:{oid[:12]}:{path}:{category}"
                for category in scan_blob(path, data, checks, history=True)
            )

    if failures:
        print("public audit failed", file=sys.stderr)
        for failure in sorted(set(failures)):
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"public audit passed: {len(tracked())} tracked files" + (" + full history" if args.history else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
