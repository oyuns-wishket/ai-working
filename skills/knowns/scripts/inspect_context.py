#!/usr/bin/env python3
"""Read-only discovery helper for the knowns project-wiki closeout."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set


CONNECTION_TERMS = (
    "wiki",
    "위키",
    "vault",
    "knowledge-base",
    "knowledge base",
    "지식베이스",
    "지식 베이스",
)
STANDARD_RULE_NAMES = (
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "SCHEMA.md",
    "GOVERNANCE.md",
    "CONTRIBUTING.md",
)
RULE_DIRECTORIES = (
    ".claude/rules",
    ".agents/rules",
    ".codex/rules",
)
RULE_NAME_TERMS = (
    "rule",
    "governance",
    "schema",
    "ingest",
    "compile",
    "maintenance",
    "runbook",
    "source-authority",
    "contradiction",
)
DESIGNATED_RULE_DIRECTORY_TERMS = (
    "rule",
    "governance",
    "policy",
    "instruction",
    "runbook",
    "schema",
    "ingest",
    "maintenance",
    "90-agent",
    "00-governance",
)
REFERENCE_SUFFIXES = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".toml"}
ENV_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]*(?:_PATH|_ROOT)\b")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
BACKTICK_PATTERN = re.compile(r"`([^`\n]+)`")
BARE_PATH_PATTERN = re.compile(r"(?<![\w])(?:~|/|\.\.?/)[^\s,;|)]+")
ENV_SUB_PATTERN = re.compile(r"\$(?:\{([A-Z][A-Z0-9_]*)\}|([A-Z][A-Z0-9_]*))")
PROJECT_WIKI_CONTEXT = (
    Path(__file__).resolve().parents[2]
    / "project-wiki-context"
    / "scripts"
    / "wiki_context.py"
)


def git_root(project: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return project.resolve()


def files_under(directory: Path) -> Iterable[Path]:
    if not directory.is_dir():
        return ()
    return (
        path
        for path in sorted(directory.rglob("*"))
        if path.is_file() and ".git" not in path.parts
    )


def collect_project_rules(root: Path) -> List[Path]:
    found: Set[Path] = set()
    for name in ("AGENTS.md", "CLAUDE.md"):
        candidate = root / name
        if candidate.is_file():
            found.add(candidate.resolve())
    for relative in RULE_DIRECTORIES:
        found.update(path.resolve() for path in files_under(root / relative))
    return sorted(found)


def has_connection_term(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in CONNECTION_TERMS)


def safe_expand_env(token: str) -> Optional[str]:
    missing = False

    def replace(match: re.Match[str]) -> str:
        nonlocal missing
        name = match.group(1) or match.group(2)
        value = os.environ.get(name)
        if value is None:
            missing = True
            return ""
        return value

    expanded = ENV_SUB_PATTERN.sub(replace, token)
    return None if missing else expanded


def normalize_path_token(token: str, base: Path) -> Optional[Path]:
    cleaned = token.strip().strip("\"'<>").rstrip(".:")
    if not cleaned or "://" in cleaned or cleaned.startswith("#"):
        return None
    expanded_env = safe_expand_env(cleaned)
    if expanded_env is None:
        return None
    expanded = Path(os.path.expanduser(expanded_env))
    if not expanded.is_absolute():
        expanded = base / expanded
    try:
        resolved = expanded.resolve()
    except OSError:
        return None
    return resolved if resolved.exists() else None


def token_candidates(fragment: str) -> Iterable[str]:
    yield fragment
    try:
        for part in shlex.split(fragment):
            yield part
    except ValueError:
        return


def extract_existing_paths(line: str, base: Path) -> Iterable[Path]:
    fragments: List[str] = []
    fragments.extend(MARKDOWN_LINK_PATTERN.findall(line))
    fragments.extend(BACKTICK_PATTERN.findall(line))
    fragments.extend(BARE_PATH_PATTERN.findall(line))
    for fragment in fragments:
        for token in token_candidates(fragment):
            resolved = normalize_path_token(token, base)
            if resolved is not None:
                yield resolved


def discover_wiki_candidates(rule_files: Sequence[Path], project_root: Path) -> List[Dict[str, object]]:
    candidates: Dict[Path, Dict[str, object]] = {}

    def canonical_target(resolved: Path) -> Optional[Path]:
        root = determine_wiki_root(resolved)
        if root == project_root:
            return None
        if (root / ".system/knowledge-contract.json").is_file():
            try:
                resolved.relative_to(root / "my-wiki")
                return None  # an explicit read link never becomes a write destination
            except ValueError:
                pass
        if resolved.is_file() and (root / ".obsidian").is_dir():
            try:
                relative = resolved.relative_to(root)
            except ValueError:
                relative = resolved
            top_level = relative.parts[0].lower() if relative.parts else ""
            if (
                top_level not in {"wiki", "raw", "evidence", "scripts"}
                and resolved.name not in STANDARD_RULE_NAMES
            ):
                return resolved
        has_wiki_shape = (root / "wiki").is_dir() or (root / "raw").is_dir() or (root / "sys-wiki").is_dir()
        named_like_wiki = any(
            term in part.lower()
            for part in root.parts
            for term in ("wiki", "vault", "knowledge")
        )
        if has_wiki_shape or named_like_wiki or (root / ".obsidian").is_dir():
            return root
        return None

    def add_candidate(resolved: Path, evidence: str, kind: str) -> None:
        target = canonical_target(resolved)
        if target is None:
            return
        item = candidates.setdefault(
            target,
            {
                "path": str(target),
                "evidence": [],
                "kind": "file" if target.is_file() else kind,
            },
        )
        if evidence not in item["evidence"]:
            item["evidence"].append(evidence)

    for rule_file in rule_files:
        try:
            lines = rule_file.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            continue
        for line_number, line in enumerate(lines, start=1):
            if not has_connection_term(line):
                continue
            evidence = f"{rule_file}:{line_number}"
            for env_name in ENV_PATTERN.findall(line):
                value = os.environ.get(env_name)
                if not value:
                    continue
                resolved = normalize_path_token(value, project_root)
                if resolved is not None:
                    add_candidate(resolved, f"{evidence} ({env_name})", "env")
            for resolved in extract_existing_paths(line, rule_file.parent):
                if resolved == rule_file.resolve():
                    continue
                add_candidate(
                    resolved,
                    evidence,
                    "file" if resolved.is_file() else "directory",
                )
    return sorted(candidates.values(), key=lambda item: str(item["path"]))


def registry_wiki_candidate(project_root: Path) -> Optional[Dict[str, object]]:
    """Resolve the machine-local registry without making it a write authority."""
    if not PROJECT_WIKI_CONTEXT.is_file():
        return None
    result = subprocess.run(
        [sys.executable, str(PROJECT_WIKI_CONTEXT), "resolve", "--project", str(project_root)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    project = payload.get("project") or {}
    namespace = (payload.get("canonical_write_target") if payload.get("registry_schema_version") == 2
                 else payload.get("namespace_path"))
    if payload.get("mode") != "wiki-bounded" or not namespace:
        return None
    target = Path(namespace).resolve()
    if not target.is_dir():
        return None
    return {
        "path": str(target),
        "evidence": [
            f"project-registry:{project.get('id', 'unknown')} ({payload.get('matched_by', 'unknown')})"
        ],
        "kind": "registry-namespace",
        "project_id": project.get("id"),
        "canonical_write_target": str(target),
        "knowledge_contract_path": payload.get("knowledge_contract_path"),
        "registry_schema_version": payload.get("registry_schema_version", 1),
    }


def discover_connected_wikis(rule_files: Sequence[Path], project_root: Path) -> List[Dict[str, object]]:
    explicit = discover_wiki_candidates(rule_files, project_root)
    registry = registry_wiki_candidate(project_root)
    if registry is None:
        return explicit
    registry_root = determine_wiki_root(Path(str(registry["path"])))
    filtered = []
    for candidate in explicit:
        try:
            same_root = determine_wiki_root(Path(str(candidate["path"]))) == registry_root
        except (OSError, ValueError):
            same_root = False
        if not same_root:
            filtered.append(candidate)
    return [registry, *filtered]


def determine_wiki_root(target: Path) -> Path:
    current = target.parent if target.is_file() else target
    if current.name.lower() in {"wiki", "raw"}:
        current = current.parent
    git_result = subprocess.run(
        ["git", "-C", str(current), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if git_result.returncode == 0 and git_result.stdout.strip():
        return Path(git_result.stdout.strip()).resolve()
    fallback = current
    for candidate in (current, *current.parents):
        if (candidate / ".obsidian").is_dir():
            return candidate.resolve()
        if (candidate / ".git").exists():
            return candidate.resolve()
        has_rules = (candidate / "AGENTS.md").is_file() or (candidate / "CLAUDE.md").is_file()
        has_wiki_shape = (candidate / "wiki").is_dir() or (candidate / "raw").is_dir()
        if has_rules and has_wiki_shape:
            return candidate.resolve()
        if candidate == candidate.parent:
            break
    return fallback.resolve()


def standard_rules_at(directory: Path) -> Iterable[Path]:
    for name in STANDARD_RULE_NAMES:
        candidate = directory / name
        if candidate.is_file():
            yield candidate.resolve()
    for child in sorted(directory.iterdir()) if directory.is_dir() else ():
        if not child.is_file():
            continue
        lowered = child.name.lower()
        if lowered.startswith(("readme", "schema", "governance", "contributing")):
            yield child.resolve()


def relative_depth(path: Path, root: Path) -> int:
    try:
        return len(path.relative_to(root).parts)
    except ValueError:
        return 999


def seed_wiki_rules(root: Path, target: Path) -> Set[Path]:
    seeds: Set[Path] = set(standard_rules_at(root))
    contract = discover_knowledge_contract(root)
    if contract:
        seeds.add(root / ".system/knowledge-contract.json")
        for key in ("schema", "template", "registry_schema"):
            path = root / contract["paths"][key]
            if path.is_file():
                seeds.add(path)
        for path in (root / ".system/scripts/kb_check.py", root / ".system/pipelines/canonical.py"):
            if path.is_file():
                seeds.add(path)
        # v2 rules are explicit; do not traverse unrelated notes or raw/candidates.
        return seeds
    target_directory = target.parent if target.is_file() else target
    if root == target_directory or root in target_directory.parents:
        relative = target_directory.relative_to(root)
        cursor = root
        for part in relative.parts:
            cursor = cursor / part
            seeds.update(standard_rules_at(cursor))
    for relative in RULE_DIRECTORIES:
        seeds.update(path.resolve() for path in files_under(root / relative))
    for directory, child_directories, filenames in os.walk(root):
        current = Path(directory)
        depth = relative_depth(current, root)
        child_directories[:] = [
            name
            for name in child_directories
            if name not in {".git", "raw", "candidate", "my-wiki", "evidence", "node_modules", ".next"}
            and depth < 5
        ]
        if depth > 5:
            continue
        relative_directory = str(current.relative_to(root)).lower()
        governed_directory = (
            "wiki/90-agent" in relative_directory
            or "wiki/00-governance" in relative_directory
        )
        for filename in filenames:
            path = current / filename
            if path.suffix.lower() not in REFERENCE_SUFFIXES:
                continue
            lowered = filename.lower()
            if governed_directory or any(term in lowered for term in RULE_NAME_TERMS):
                seeds.add(path.resolve())
    return seeds


def explicit_references(rule_file: Path, root: Path) -> Iterable[Path]:
    try:
        text = rule_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ()
    found: Set[Path] = set()
    for line in text.splitlines():
        fragments = MARKDOWN_LINK_PATTERN.findall(line) + BACKTICK_PATTERN.findall(line)
        for fragment in fragments:
            for token in token_candidates(fragment):
                candidates = (rule_file.parent, root)
                for base in candidates:
                    resolved = normalize_path_token(token, base)
                    if resolved is None:
                        continue
                    if resolved.is_file() and resolved.suffix.lower() in REFERENCE_SUFFIXES:
                        found.add(resolved)
                    elif resolved.is_dir():
                        try:
                            relative = resolved.relative_to(root)
                        except ValueError:
                            break
                        relative_text = str(relative).lower()
                        if (
                            not {"raw", "evidence"}.intersection(
                                part.lower() for part in relative.parts
                            )
                            and any(
                                term in relative_text
                                for term in DESIGNATED_RULE_DIRECTORY_TERMS
                            )
                        ):
                            found.update(
                                path.resolve()
                                for path in files_under(resolved)
                                if path.suffix.lower() in REFERENCE_SUFFIXES
                            )
                    break
    return sorted(found)


def collect_wiki_rules(root: Path, target: Path) -> List[Path]:
    pending = list(seed_wiki_rules(root, target))
    collected: Set[Path] = set()
    while pending and len(collected) < 250:
        current = pending.pop(0).resolve()
        if current in collected or not current.is_file():
            continue
        collected.add(current)
        for referenced in explicit_references(current, root):
            if referenced not in collected:
                pending.append(referenced)
    return sorted(collected)


def discover_knowledge_contract(root: Path) -> Optional[dict]:
    path = root / ".system/knowledge-contract.json"
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("schema_version") != 2 or value["paths"]["canonical"] != "sys-wiki" or value["paths"]["manual"] != "my-wiki":
            raise ValueError("unsupported knowledge contract")
        for key in ("canonical", "candidate", "manual", "schema", "template", "registry", "registry_schema"):
            relative = Path(value["paths"][key])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("unsafe contract path")
            (root / relative).resolve().relative_to(root.resolve())
        return value
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise ValueError(f"Invalid owning knowledge contract: {error}") from error


def validate_canonical_write_target(root: Path, target: Path, allowed: Path) -> None:
    """A bound manual note and a read scope are never a canonical write grant."""
    canonical = (root / "sys-wiki").resolve()
    try:
        allowed.resolve().relative_to(canonical)
        target.resolve().relative_to(allowed.resolve())
    except ValueError as error:
        raise ValueError("Write target must stay inside the registered sys-wiki canonical target") from error
    if "my-wiki" in target.relative_to(root).parts:
        raise ValueError("my-wiki is user-owned and never an ingest target")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="Active project path")
    parser.add_argument("--wiki", help="Selected wiki directory or mapped note")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_input = Path(os.path.expanduser(args.project)).resolve()
    if not project_input.exists():
        raise SystemExit(f"Project path does not exist: {project_input}")
    project_root = git_root(project_input)
    project_rules = collect_project_rules(project_root)
    result: Dict[str, object] = {
        "project_root": str(project_root),
        "project_rules": [str(path) for path in project_rules],
        "wiki_candidates": discover_connected_wikis(project_rules, project_root),
        "wiki_target": None,
        "wiki_root": None,
        "wiki_rules": [],
        "read_only": True,
    }
    if args.wiki:
        wiki_target = Path(os.path.expanduser(args.wiki)).resolve()
        if not wiki_target.exists():
            raise SystemExit(f"Wiki path does not exist: {wiki_target}")
        wiki_root = determine_wiki_root(wiki_target)
        contract = discover_knowledge_contract(wiki_root)
        if contract:
            registry = registry_wiki_candidate(project_root)
            if not registry or registry.get("registry_schema_version") != 2:
                raise SystemExit("No explicit canonical write target for this v2 wiki")
            allowed = Path(str(registry["canonical_write_target"]))
            validate_canonical_write_target(wiki_root, wiki_target, allowed)
            result["canonical_write_target"] = str(allowed)
            result["knowledge_contract"] = contract
        result.update(
            {
                "wiki_target": str(wiki_target),
                "wiki_root": str(wiki_root),
                "wiki_rules": [
                    str(path) for path in collect_wiki_rules(wiki_root, wiki_target)
                ],
            }
        )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"project_root: {result['project_root']}")
        for candidate in result["wiki_candidates"]:
            print(f"wiki_candidate: {candidate['path']}")
        if result["wiki_root"]:
            print(f"wiki_root: {result['wiki_root']}")
            for rule in result["wiki_rules"]:
                print(f"wiki_rule: {rule}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
