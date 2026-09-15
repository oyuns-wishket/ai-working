#!/usr/bin/env python3
"""Resolve Git projects to bounded, fail-closed context-registry context."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


REGISTRY_REL = Path("registry/project-registry.json")
EXCLUDED_PARTS = {"raw", "derived", ".runtime", "omc-inbox", "80-observations", "candidate", ".system"}
WORD_RE = re.compile(r"[0-9A-Za-z가-힣][0-9A-Za-z가-힣._/-]*")
FRONTMATTER_KEY = re.compile(r"^([a-z_]+):\s*(.*?)\s*$")
SOURCE_REF_RE = re.compile(r"^repo:([^@]+)@([0-9a-fA-F]{7,40})(?:/(.+))?$")


class ContextError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitIdentity:
    project_path: Path
    git_root: Path
    common_dir: Path
    remotes: tuple[str, ...]
    normalized_remotes: tuple[str, ...]


def run_git(project: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise ContextError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def try_git(project: Path, *args: str) -> tuple[bool, str]:
    result = subprocess.run(
        ["git", "-C", str(project), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout.strip()


def normalize_remote(remote: str | None) -> str:
    if remote is None:
        return ""
    value = remote.strip()
    if not value:
        return ""
    if re.match(r"^[^/@:]+@[^:]+:.+$", value):
        _, remainder = value.split("@", 1)
        host, path = remainder.split(":", 1)
        return f"{host.lower()}/{path.removesuffix('.git').strip('/').lower()}"
    if "://" in value:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower()
        path = parsed.path.removesuffix(".git").strip("/").lower()
        return f"{host}/{path}" if host and path else ""
    path = Path(value).expanduser()
    if path.is_absolute():
        return f"local/{path.resolve().as_posix().lower()}"
    return value.removesuffix(".git").strip("/").lower()


def git_identity(project: Path) -> GitIdentity:
    requested = project.expanduser().resolve()
    root = Path(run_git(requested, "rev-parse", "--show-toplevel")).resolve()
    common_raw = run_git(requested, "rev-parse", "--git-common-dir")
    common = Path(common_raw)
    if not common.is_absolute():
        common = (root / common).resolve()
    names = run_git(requested, "remote").splitlines()
    remotes: list[str] = []
    for name in (["origin"] if "origin" in names else []) + sorted(n for n in names if n != "origin"):
        try:
            value = run_git(requested, "remote", "get-url", name)
        except ContextError:
            continue
        if value and value not in remotes:
            remotes.append(value)
    normalized = tuple(item for item in (normalize_remote(r) for r in remotes) if item)
    return GitIdentity(requested, root, common, tuple(remotes), normalized)


def repository_state(identity: GitIdentity) -> dict:
    branch_ok, branch = try_git(identity.git_root, "branch", "--show-current")
    head_ok, head = try_git(identity.git_root, "rev-parse", "HEAD")
    upstream_ok, upstream = try_git(
        identity.git_root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"
    )
    ahead = behind = None
    if upstream_ok:
        counts_ok, counts = try_git(
            identity.git_root, "rev-list", "--left-right", "--count", f"HEAD...{upstream}"
        )
        if counts_ok:
            left, right = counts.split()
            ahead, behind = int(left), int(right)
    status_ok, status = try_git(identity.git_root, "status", "--porcelain")
    dirty_count = len(status.splitlines()) if status_ok and status else 0
    return {
        "branch": branch if branch_ok and branch else None,
        "head": head if head_ok else None,
        "upstream": upstream if upstream_ok else None,
        "ahead": ahead,
        "behind": behind,
        "diverged": bool(ahead and behind),
        "dirty_count": dirty_count,
    }


def find_wiki_root(explicit: str | None = None) -> Path:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("AI_WORKING_CONTEXT_REGISTRY_PATH"):
        candidates.append(Path(os.environ["AI_WORKING_CONTEXT_REGISTRY_PATH"]))
    candidates.append(Path.home() / ".config" / "ai-working" / "context-registry")
    for candidate in candidates:
        root = candidate.expanduser().resolve()
        pointer = root / "registry/knowledge-root.json"
        if pointer.is_file():
            try:
                value = json.loads(pointer.read_text(encoding="utf-8"))
                root = Path(value["knowledge_root"]).expanduser().resolve()
                if not knowledge_contract(root):
                    raise ContextError("adapter points to a missing knowledge contract")
            except (OSError, KeyError, TypeError, ValueError) as error:
                raise ContextError(f"invalid knowledge root adapter: {error}") from error
        if registry_path(root).is_file():
            return root
    checked = ", ".join(str(p.expanduser()) for p in candidates)
    raise ContextError(f"registry not found; checked: {checked}")


def load_registry(root: Path) -> dict:
    try:
        data = json.loads(registry_path(root).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContextError(f"invalid registry: {error}") from error
    if not isinstance(data, dict) or data.get("schema_version") not in (1, 2) or not isinstance(data.get("projects"), list):
        raise ContextError("unsupported registry schema")
    if not isinstance(data.get("defaults", {}), dict):
        raise ContextError("registry defaults must be an object")
    defaults = data.get("defaults", {}).get("retrieval", {})
    if not isinstance(defaults, dict):
        raise ContextError("registry defaults.retrieval must be an object")
    allowed_connections = {"connected", "common-only", "archived", "excluded"}
    for entry in data["projects"]:
        if not isinstance(entry, dict):
            raise ContextError("registry projects must be objects")
        if not isinstance(entry.get("canonical_remote"), (str, type(None))):
            raise ContextError("registry canonical_remote must be a string or null")
        for key in ("remote_aliases", "local_aliases"):
            value = entry.get(key)
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                raise ContextError(f"registry {key} must be a string array")
        if entry.get("connection_status") not in allowed_connections:
            raise ContextError("registry connection_status is invalid")
        if not isinstance(entry.get("wiki_namespace"), (str, type(None))):
            raise ContextError("registry wiki_namespace must be a string or null")
        if not isinstance(entry.get("retrieval", {}), dict):
            raise ContextError("registry retrieval must be an object")
        retrieval = {**defaults, **entry.get("retrieval", {})}
        entry["retrieval"] = retrieval
        if not isinstance(retrieval, dict):
            raise ContextError("registry retrieval must be an object")
        for key, default, maximum in (
            ("max_documents", 4, 8),
            ("max_total_bytes", 80000, 250000),
        ):
            value = retrieval.get(key, default)
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= maximum:
                raise ContextError(f"registry retrieval {key} is invalid")
        pinned = retrieval.get("pinned", [])
        if not isinstance(pinned, list) or any(not isinstance(item, str) for item in pinned):
            raise ContextError("registry retrieval pinned must be a string array")
        intent_routes = retrieval.get("intent_routes", {})
        if not isinstance(intent_routes, dict):
            raise ContextError("registry retrieval intent_routes must be an object")
        for intent, route in intent_routes.items():
            if not isinstance(intent, str) or not isinstance(route, dict):
                raise ContextError("registry intent route is invalid")
            terms = route.get("terms")
            documents = route.get("documents")
            if (
                not isinstance(terms, list)
                or not terms
                or any(not isinstance(item, str) or len(item) < 2 for item in terms)
                or not isinstance(documents, list)
                or not documents
                or any(not isinstance(item, str) for item in documents)
            ):
                raise ContextError(f"registry intent route {intent!r} is invalid")
    if data["schema_version"] == 2:
        validate_registry_v2(data)
    ids = [entry.get("id") for entry in data["projects"]]
    if any(not isinstance(item, str) or not item for item in ids) or len(ids) != len(set(ids)):
        raise ContextError("registry project ids must be non-empty and unique")
    return data


def entry_identities(entry: dict) -> set[str]:
    values = [entry.get("canonical_remote", ""), *entry.get("remote_aliases", [])]
    return {normalized for value in values if (normalized := normalize_remote(value))}


def resolve_entry(registry: dict, identity: GitIdentity) -> tuple[dict | None, str]:
    remote_matches = []
    for entry in registry["projects"]:
        overlap = set(identity.normalized_remotes) & entry_identities(entry)
        if overlap:
            remote_matches.append((entry, sorted(overlap)))
    if len(remote_matches) == 1:
        return remote_matches[0][0], f"remote:{remote_matches[0][1][0]}"
    if len(remote_matches) > 1:
        raise ContextError("one Git identity matches multiple registry entries")

    aliases = []
    for entry in registry["projects"]:
        if identity.git_root.name in entry.get("local_aliases", []):
            aliases.append(entry)
    if len(aliases) == 1 and not identity.normalized_remotes:
        return aliases[0], f"local-alias:{identity.git_root.name}"
    return None, "unmatched"


def resolve(project: Path, wiki_root: str | None = None) -> dict:
    root = find_wiki_root(wiki_root)
    registry = load_registry(root)
    identity = git_identity(project)
    entry, matched_by = resolve_entry(registry, identity)
    base = {
        "project_path": str(identity.project_path),
        "git_root": str(identity.git_root),
        "git_common_dir": str(identity.common_dir),
        "remotes": list(identity.remotes),
        "normalized_remotes": list(identity.normalized_remotes),
        "wiki_root": str(root),
        "managed": entry is not None,
        "matched_by": matched_by,
        "repo_state": repository_state(identity),
    }
    if entry is None:
        return {**base, "mode": "repo-only", "reason": "registry entry not found"}
    if registry["schema_version"] == 2:
        return resolve_v2(base, entry, root)
    namespace = entry.get("wiki_namespace")
    namespace_path = (root / namespace).resolve() if namespace else None
    index_path = namespace_path / "index.md" if namespace_path else None
    connected = entry.get("connection_status") == "connected"
    contained = False
    if namespace_path:
        try:
            namespace_path.relative_to((root / "wiki").resolve(strict=True))
            contained = True
        except (OSError, ValueError):
            pass
    if connected and not contained:
        return {
            **base,
            "project": entry,
            "mode": "repo-only",
            "reason": "registry namespace escapes or is outside wiki",
            "namespace_path": str(namespace_path) if namespace_path else None,
            "index_path": str(index_path) if index_path else None,
        }
    return {
        **base,
        "project": entry,
        "mode": "wiki-bounded" if connected else "repo-only",
        "namespace_path": str(namespace_path) if namespace_path else None,
        "index_path": str(index_path) if index_path else None,
    }


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    metadata: dict[str, str] = {}
    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = index
            break
        match = FRONTMATTER_KEY.match(line)
        if match:
            metadata[match.group(1)] = match.group(2).strip().strip("\"'")
    if end is None:
        return {}, text
    return metadata, "\n".join(lines[end + 1 :])


def frontmatter_list(path: Path, key: str) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    items: list[str] = []
    active = False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = FRONTMATTER_KEY.match(line)
        if match:
            active = match.group(1) == key
            if active and match.group(2).startswith("["):
                try:
                    value = json.loads(match.group(2))
                    return value if isinstance(value, list) and all(isinstance(item, str) for item in value) else []
                except ValueError:
                    return []
            continue
        if active:
            item = re.match(r'^\s+-\s+"?(.+?)"?\s*$', line)
            if item:
                items.append(item.group(1))
            elif line.strip():
                active = False
    return items


def safe_document(path: Path, namespace: Path, today: dt.date) -> tuple[bool, str, dict[str, str], str]:
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(namespace.resolve(strict=True))
    except (OSError, ValueError):
        return False, "path escapes namespace", {}, ""
    if any(part in EXCLUDED_PARTS for part in resolved.parts):
        return False, "excluded corpus", {}, ""
    try:
        metadata, body = parse_frontmatter(resolved)
    except (OSError, UnicodeDecodeError):
        return False, "unreadable", {}, ""
    if metadata.get("status") != "canonical":
        return False, f"status:{metadata.get('status', 'missing')}", metadata, body
    try:
        review_by = dt.date.fromisoformat(metadata["review_by"])
    except (KeyError, ValueError):
        return False, "invalid review_by", metadata, body
    if review_by < today:
        return False, f"overdue:{review_by.isoformat()}", metadata, body
    return True, "canonical-current", metadata, body


def tokens(value: str) -> set[str]:
    return {match.group(0).lower() for match in WORD_RE.finditer(value) if len(match.group(0)) > 1}


def matched_intents(policy: dict, query: str) -> tuple[list[str], set[str]]:
    query_lower = query.lower()
    matches: list[str] = []
    documents: set[str] = set()
    routes = policy.get("intent_routes", {})
    if not isinstance(routes, dict):
        return matches, documents
    for name, route in routes.items():
        if not isinstance(route, dict):
            continue
        terms = [str(term).lower() for term in route.get("terms", []) if len(str(term)) > 1]
        if terms and any(term in query_lower for term in terms):
            matches.append(str(name))
            documents.update(str(path) for path in route.get("documents", []))
    return sorted(matches), documents


def source_reference_health(path: Path, resolved: dict) -> dict:
    aliases = set(resolved["project"].get("local_aliases", []))
    aliases.add(Path(resolved["git_root"]).name)
    project_id = resolved["project"].get("id", "")
    if "/" in project_id:
        aliases.add(project_id.rsplit("/", 1)[-1])
        aliases.add(project_id)
        aliases.add(project_id.split("/", 1)[1])

    checked = []
    for reference in frontmatter_list(path, "source_refs"):
        match = SOURCE_REF_RE.match(reference)
        if not match:
            if any(
                reference == f"repo:{alias}"
                or reference.startswith(f"repo:{alias}@")
                or reference.startswith(f"repo:{alias}/")
                for alias in aliases
            ):
                checked.append(
                    {
                        "reference": reference,
                        "commit_exists": False,
                        "path_exists": False,
                        "ancestor_of_head": None,
                        "changed_since": None,
                        "reason": "malformed-reference",
                    }
                )
            continue
        if match.group(1) not in aliases:
            continue
        _, sha, referenced_path = match.groups()
        if referenced_path:
            reference_path = Path(referenced_path)
            if reference_path.is_absolute() or ".." in reference_path.parts:
                checked.append(
                    {
                        "reference": reference,
                        "commit_exists": False,
                        "path_exists": False,
                        "ancestor_of_head": None,
                        "changed_since": None,
                        "reason": "unsafe-path",
                    }
                )
                continue
        commit_ok, _ = try_git(Path(resolved["git_root"]), "cat-file", "-e", f"{sha}^{{commit}}")
        path_ok = None
        changed_since = None
        ancestor = None
        if commit_ok:
            ancestor, _ = try_git(Path(resolved["git_root"]), "merge-base", "--is-ancestor", sha, "HEAD")
            if referenced_path:
                path_ok, _ = try_git(
                    Path(resolved["git_root"]), "cat-file", "-e", f"{sha}:{referenced_path}"
                )
                if path_ok and ancestor:
                    unchanged, _ = try_git(
                        Path(resolved["git_root"]), "diff", "--quiet", f"{sha}..HEAD", "--", referenced_path
                    )
                    changed_since = not unchanged
        checked.append(
            {
                "reference": reference,
                "commit_exists": commit_ok,
                "path_exists": path_ok,
                "ancestor_of_head": ancestor,
                "changed_since": changed_since,
            }
        )
    return {
        "checked": len(checked),
        "missing_commits": sum(not item["commit_exists"] for item in checked),
        "missing_paths": sum(item["path_exists"] is False for item in checked),
        "non_ancestor_commits": sum(item["ancestor_of_head"] is False for item in checked),
        "changed_paths": sum(item["changed_since"] is True for item in checked),
        "details": checked,
    }


def namespace_health(
    resolved: dict,
    today: dt.date | None = None,
    source_cache: dict[str, dict] | None = None,
) -> dict:
    today = today or dt.date.today()
    source_cache = source_cache if source_cache is not None else {}
    namespace = Path(resolved["namespace_path"])
    policy = resolved["project"].get("retrieval", {})
    pinned = set(policy.get("pinned", []))
    counts = {
        "documents": 0,
        "canonical_current": 0,
        "canonical_overdue": 0,
        "provisional": 0,
        "contested": 0,
        "deprecated": 0,
    }
    pinned_rows = []
    for path in sorted(namespace.rglob("*.md")):
        rel = path.relative_to(namespace).as_posix()
        ok, reason, metadata, _ = safe_document(path, namespace, today)
        status = metadata.get("status", "missing")
        counts["documents"] += 1
        if status == "canonical":
            try:
                overdue = dt.date.fromisoformat(metadata["review_by"]) < today
            except (KeyError, ValueError):
                overdue = True
            counts["canonical_overdue" if overdue else "canonical_current"] += 1
        elif status in counts:
            counts[status] += 1
        if rel in pinned:
            if metadata:
                cache_key = str(path)
                if cache_key not in source_cache:
                    source_cache[cache_key] = source_reference_health(path, resolved)
                source_health = source_cache[cache_key]
            else:
                source_health = {
                    "checked": 0,
                    "missing_commits": 0,
                    "missing_paths": 0,
                    "non_ancestor_commits": 0,
                    "changed_paths": 0,
                    "details": [],
                }
            source_summary = {key: value for key, value in source_health.items() if key != "details"}
            pinned_rows.append(
                {"path": rel, "available": ok, "reason": reason, "source_health": source_summary}
            )
    found_pinned = {row["path"] for row in pinned_rows}
    for missing in sorted(pinned - found_pinned):
        pinned_rows.append({"path": missing, "available": False, "reason": "missing"})

    reasons = []
    if counts["canonical_overdue"]:
        reasons.append("canonical-overdue")
    if any(not row["available"] for row in pinned_rows):
        reasons.append("pinned-unavailable")
    if any(
        row.get("source_health", {}).get("missing_commits", 0)
        or row.get("source_health", {}).get("missing_paths", 0)
        for row in pinned_rows
    ):
        reasons.append("pinned-source-invalid")
    return {
        **counts,
        "canonical_total": counts["canonical_current"] + counts["canonical_overdue"],
        "pinned": pinned_rows,
        "status": "degraded" if reasons else "healthy",
        "reasons": reasons,
    }


def routed_documents(resolved: dict, query: str) -> dict:
    if resolved.get("registry_schema_version") == 2:
        return routed_v2(resolved, query)
    if resolved.get("mode") != "wiki-bounded":
        return {**resolved, "documents": [], "route_reason": resolved.get("reason", "repo-only")}
    namespace = Path(resolved["namespace_path"])
    index = Path(resolved["index_path"])
    if resolved.get("wiki_root"):
        try:
            namespace.resolve(strict=True).relative_to(
                (Path(resolved["wiki_root"]) / "wiki").resolve(strict=True)
            )
        except (OSError, ValueError):
            return {
                **resolved,
                "mode": "repo-only",
                "documents": [],
                "route_reason": "namespace escapes or is outside wiki",
            }
    if not index.is_file():
        return {**resolved, "mode": "repo-only", "documents": [], "route_reason": "namespace index missing"}

    policy = resolved["project"].get("retrieval", {})
    max_documents = max(1, min(int(policy.get("max_documents", 4)), 8))
    max_bytes = max(1, min(int(policy.get("max_total_bytes", 80000)), 250000))
    query_tokens = tokens(query)
    intents, intent_documents = matched_intents(policy, query)
    today = dt.date.today()
    rejected = []
    candidates = []
    index_document = None
    source_cache: dict[str, dict] = {}

    def cached_source_health(path: Path) -> dict:
        key = str(path)
        if key not in source_cache:
            source_cache[key] = source_reference_health(path, resolved)
        return source_cache[key]

    for path in sorted(namespace.rglob("*.md")):
        ok, reason, metadata, body = safe_document(path, namespace, today)
        rel = path.relative_to(namespace).as_posix()
        if not ok:
            rejected.append({"path": rel, "reason": reason})
            continue
        title = metadata.get("title", path.stem)
        haystack = tokens(f"{rel} {title} {body[:12000]}")
        overlap = sorted(query_tokens & haystack)
        score = len(overlap) * 10
        if path == index:
            source_health = cached_source_health(path)
            if source_health["missing_commits"] or source_health["missing_paths"]:
                rejected.append({"path": rel, "reason": "invalid-source-ref"})
                continue
            index_document = {
                "path": str(path),
                "relative_path": rel,
                "title": title,
                "bytes": len(path.read_bytes()),
                "score": score,
                "matched_terms": overlap[:12],
                "selection_reasons": ["namespace-index"],
                "source_health": source_health,
            }
            continue
        reasons = []
        if overlap:
            reasons.append("query-overlap")
        if rel in intent_documents:
            score += 30
            reasons.append("intent-route")
        if rel in policy.get("pinned", []) and score > 0:
            score += 2
            reasons.append("pinned-tiebreak")
        candidates.append((score, len(path.read_bytes()), rel, path, title, overlap, reasons))

    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    selected = []
    used_bytes = index_document["bytes"] if index_document else 0
    for score, size, rel, path, title, overlap, reasons in candidates:
        if score <= 0 or len(selected) >= max_documents or used_bytes + size > max_bytes:
            continue
        source_health = cached_source_health(path)
        if source_health["missing_commits"] or source_health["missing_paths"]:
            rejected.append({"path": rel, "reason": "invalid-source-ref"})
            continue
        selected.append(
            {
                "path": str(path),
                "relative_path": rel,
                "title": title,
                "bytes": size,
                "score": score,
                "matched_terms": overlap[:12],
                "selection_reasons": reasons,
                "source_health": source_health,
            }
        )
        used_bytes += size
    if index_document is None:
        return {
            **resolved,
            "mode": "repo-only",
            "documents": [],
            "route_reason": "no current canonical namespace index",
            "rejected": rejected,
        }
    if index_document["bytes"] > max_bytes:
        return {
            **resolved,
            "mode": "repo-only",
            "documents": [],
            "route_reason": "namespace index exceeds max_total_bytes",
            "rejected": rejected,
        }
    context_documents = [index_document, *selected]
    return {
        **resolved,
        "index_document": index_document,
        "query_documents": selected,
        "documents": context_documents,
        "index_counts_toward_document_limit": False,
        "route_reason": "bounded canonical retrieval" if selected else "index-only; no relevant canonical document",
        "query": query,
        "matched_intents": intents,
        "selected_bytes": used_bytes,
        "rejected": rejected,
        "knowledge_health": namespace_health(resolved, today, source_cache),
    }


def discover_repositories(workspace: Path) -> list[GitIdentity]:
    identities = []
    for child in sorted(workspace.expanduser().resolve().iterdir(), key=lambda item: item.name.lower()):
        if not child.is_dir() or child.name.startswith(".worktrees"):
            continue
        try:
            identity = git_identity(child)
        except ContextError:
            continue
        if identity.git_root != child.resolve():
            continue
        identities.append(identity)
    return identities


def audit_workspace(workspace: Path, wiki_root: str | None = None) -> dict:
    root = find_wiki_root(wiki_root)
    registry = load_registry(root)
    rows = []
    unmatched = []
    seen_ids: set[str] = set()
    for identity in discover_repositories(workspace):
        entry, matched_by = resolve_entry(registry, identity)
        row = {
            "local_name": identity.git_root.name,
            "git_root": str(identity.git_root),
            "normalized_remotes": list(identity.normalized_remotes),
            "managed": entry is not None,
            "matched_by": matched_by,
            "project_id": entry.get("id") if entry else None,
            "connection_status": entry.get("connection_status") if entry else None,
        }
        rows.append(row)
        if entry:
            seen_ids.add(entry["id"])
        else:
            unmatched.append(row)
    return {
        "workspace": str(workspace.expanduser().resolve()),
        "discovered_local_roots": len(rows),
        "matched_registry_projects": len(seen_ids),
        "unclassified_count": len(unmatched),
        "unclassified": unmatched,
        "repositories": rows,
    }


def doctor(project: Path, wiki_root: str | None = None) -> dict:
    result = resolve(project, wiki_root)
    if result.get("registry_schema_version") == 2:
        route = routed_v2(result, "")
        return {**route, "healthy": route.get("mode") == "wiki-bounded",
                "status": "healthy" if route.get("mode") == "wiki-bounded" and not route.get("rejected") else "degraded",
                "checks": [{"name": "scoped-routing", "ok": route.get("mode") == "wiki-bounded"}]}
    checks = []
    route = None
    checks.append({"name": "registry-match", "ok": result["managed"], "detail": result["matched_by"]})
    if not result["managed"]:
        return {
            **result,
            "healthy": False,
            "status": "unhealthy",
            "checks": checks,
            "knowledge_health": None,
        }
    entry = result["project"]
    checks.append(
        {
            "name": "explicit-classification",
            "ok": entry.get("connection_status") in {"connected", "common-only", "archived", "excluded"},
            "detail": entry.get("connection_status"),
        }
    )
    if entry.get("connection_status") == "connected":
        namespace = Path(result["namespace_path"]) if result.get("namespace_path") else None
        root = Path(result["wiki_root"])
        try:
            namespace.resolve(strict=True).relative_to((root / "wiki").resolve(strict=True))
            contained = True
        except (AttributeError, OSError, ValueError):
            contained = False
        checks.append({"name": "namespace-contained", "ok": contained, "detail": str(namespace)})
        index_ok = bool(result.get("index_path")) and Path(result["index_path"]).is_file()
        checks.append({"name": "namespace-index", "ok": index_ok, "detail": result.get("index_path")})
        route = routed_documents(result, "project overview current architecture")
        checks.append(
            {
                "name": "safe-route",
                "ok": route.get("mode") == "wiki-bounded" and bool(route.get("documents")),
                "detail": route.get("route_reason"),
            }
        )
    connection_healthy = all(check["ok"] for check in checks)
    quality = (
        route.get("knowledge_health") if route and route.get("knowledge_health") else namespace_health(result)
        if entry.get("connection_status") == "connected" and result.get("mode") == "wiki-bounded"
        else None
    )
    status = "unhealthy" if not connection_healthy else (quality or {}).get("status", "healthy")
    return {
        **result,
        "healthy": connection_healthy,
        "status": status,
        "checks": checks,
        "knowledge_health": quality,
    }


def compact_hook(result: dict) -> str:
    if not result.get("managed"):
        return "project-wiki-context: unmanaged; use repository context only"
    project = result["project"]
    if result.get("mode") != "wiki-bounded":
        return f"project-wiki-context: {project['id']} [{project['connection_status']}]; use repository context only"
    return (
        f"project-wiki-context: {project['id']} [connected]; "
        f"namespace={project['wiki_namespace']}; index={result['index_path']}; "
        "run project-wiki-context route for bounded canonical context"
    )


def print_result(value: dict | str, compact: bool) -> None:
    if isinstance(value, str):
        print(value)
    elif compact:
        print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(value, ensure_ascii=False, indent=2))


# Registry v2 keeps routing, write ownership, and user-owned notes separate.
def safe_relative(value: object) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute() or ".." in Path(value).parts:
        raise ContextError("unsafe registry/contract path")
    return Path(value)


def validate_sections(value: object) -> list[dict]:
    if not isinstance(value, list) or len(value) > 12:
        raise ValueError("canonical sections must contain at most twelve entries")
    seen = set()
    for section in value:
        if not isinstance(section, dict) or (not {"slug", "title"} <= set(section) or set(section) - {"slug", "title", "description", "terms"}):
            raise ValueError("invalid canonical section fields")
        slug = section["slug"]
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or len(slug) > 64 or slug in seen or slug in {"raw", "candidate", "my-wiki", "sys-wiki", "aidp", "index"}:
            raise ValueError("unsafe or duplicate canonical section slug")
        seen.add(slug)
        for key, maximum in (("title", 80), ("description", 500)):
            text = section.get(key, "")
            if not isinstance(text, str) or (key == "title" and not text.strip()) or len(text) > maximum or any(ord(c) < 32 for c in text):
                raise ValueError("invalid canonical section text")
        terms = section.get("terms", [])
        if not isinstance(terms, list) or len(terms) > 8 or any(not isinstance(t, str) or not t.strip() or len(t) > 80 or any(ord(c) < 32 for c in t) for t in terms):
            raise ValueError("invalid canonical section terms")
        if len(terms) != len({term.strip().casefold() for term in terms}):
            raise ValueError("duplicate canonical section terms")
    return value


def no_symlink_directory(root: Path, relative: Path) -> Path:
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError("canonical directory is a symlink or not a directory")
    path.resolve().relative_to(root.resolve())
    return path


def scoped_directories(root: Path, scope: dict, contract: dict | None) -> list[Path]:
    """An existing scope grants access; the contract only bounds its child directories."""
    namespace = scope["path"]
    sections = (contract or {}).get("canonical_sections", {}).get(namespace)
    if sections is None:
        relative = Path(namespace)
        own_project = (len(relative.parts) == 3 and relative.parts[:2] == ("sys-wiki", "aidp")
                       and relative.parts[2] == scope["customer_scope"] and scope["customer_scope"] != "common")
        sections = (contract or {}).get("default_project_sections", []) if own_project else []
    return [no_symlink_directory(root, Path(namespace)),
            *(no_symlink_directory(root, Path(namespace) / section["slug"]) for section in sections)]


def knowledge_contract(root: Path) -> dict | None:
    path = root / ".system/knowledge-contract.json"
    if not path.is_file():
        return None
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
        paths = contract["paths"]
        if contract["schema_version"] != 2 or not isinstance(paths, dict):
            raise ValueError("unsupported contract")
        for key in ("canonical", "candidate", "manual", "registry", "registry_schema", "schema", "template"):
            relative = safe_relative(paths[key])
            (root / relative).resolve().relative_to(root.resolve())
        for key, expected in (("canonical", "sys-wiki"), ("candidate", "candidate"), ("manual", "my-wiki")):
            if paths[key] != expected:
                raise ValueError("invalid v2 knowledge roots")
        sections = contract.get("canonical_sections", {})
        if not isinstance(sections, dict) or len(sections) > 1000:
            raise ValueError("canonical_sections must be a namespace map")
        for namespace, rows in sections.items():
            relative = safe_relative(namespace)
            parts = relative.parts
            if not parts or parts[-1] in {"raw", "candidate", "my-wiki", "sys-wiki", "aidp", "index"} or namespace != relative.as_posix() or not (
                    (len(parts) == 3 and parts[:2] == ("sys-wiki", "aidp"))
                    or (len(parts) == 2 and parts[0] == "sys-wiki" and parts[1] != "aidp")) or any(
                    not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", part) or len(part) > 64 for part in parts[1:]):
                raise ValueError("canonical section namespace must name a canonical project root")
            no_symlink_directory(root, relative)
            for section in validate_sections(rows):
                no_symlink_directory(root, relative / section["slug"])
        if "default_project_sections" in contract:
            validate_sections(contract["default_project_sections"])
        return contract
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise ContextError(f"invalid knowledge contract: {error}") from error


def registry_path(root: Path) -> Path:
    contract = knowledge_contract(root)
    if contract:
        return root / contract["paths"]["registry"]
    return root / REGISTRY_REL


def domain(value: str) -> str:
    return value.split("/", 1)[0]


def validate_registry_v2(data: dict) -> None:
    for entry in data["projects"]:
        if not isinstance(entry.get("security_domain"), str):
            raise ContextError("v2 project security_domain required")
        scopes = entry.get("read_scopes")
        bindings = entry.get("manual_read_bindings")
        if not isinstance(scopes, list) or not isinstance(bindings, list):
            raise ContextError("v2 read scopes and manual bindings must be arrays")
        if entry["connection_status"] in {"excluded", "archived"} and (scopes or bindings or entry.get("canonical_write_target")):
            raise ContextError("excluded project must not grant knowledge access")
        for scope in scopes:
            if not isinstance(scope, dict):
                raise ContextError("invalid read scope")
            path = safe_relative(scope.get("path"))
            if path.parts[0] != "sys-wiki" or scope.get("recursive") is not False:
                raise ContextError("v2 canonical scopes must be flat sys-wiki directories")
            validate_scope_identity(entry, scope)
        ids = []
        for binding in bindings:
            if not isinstance(binding, dict) or not isinstance(binding.get("id"), str) or not binding["id"]:
                raise ContextError("manual binding requires a stable document id")
            path = safe_relative(binding.get("path"))
            if path.parts[0] != "my-wiki" or path.suffix != ".md":
                raise ContextError("manual binding must name one my-wiki markdown file")
            validate_scope_identity(entry, binding)
            ids.append(binding["id"])
        if len(ids) != len(set(ids)):
            raise ContextError("duplicate manual note binding")
        target = entry.get("canonical_write_target")
        if target is not None:
            path = safe_relative(target)
            if entry["connection_status"] != "connected" or path.parts[0] != "sys-wiki":
                raise ContextError("canonical write target must be connected sys-wiki")
            if target != entry.get("wiki_namespace"):
                raise ContextError("legacy namespace must equal canonical write target")
            if not any(s["path"] == target and s["customer_scope"] == entry.get("customer_scope") for s in scopes):
                raise ContextError("write target must be the project's own read scope")
        elif entry["connection_status"] == "connected":
            raise ContextError("connected entry requires canonical_write_target")


def validate_scope_identity(entry: dict, scope: dict) -> None:
    scope_domain = scope.get("security_domain")
    customer = scope.get("customer_scope")
    if scope_domain not in {"work", "personal", "public"} or domain(entry["security_domain"]) != scope_domain:
        raise ContextError("read scope security domain differs from project")
    if not isinstance(customer, str) or not customer:
        raise ContextError("read scope customer identity required")
    if customer not in {"common", entry.get("customer_scope")}:
        raise ContextError("cross-customer read scope")
    path = safe_relative(scope["path"])
    if path.parts[0] == "sys-wiki":
        if customer == "common" and tuple(path.parts) != ("sys-wiki", "aidp"):
            raise ContextError("common scope must be flat AIDP root")
        if customer != "common" and tuple(path.parts) != ("sys-wiki", "aidp", customer):
            raise ContextError("project scope path must match customer identity")


def resolve_v2(base: dict, entry: dict, root: Path) -> dict:
    active = entry["connection_status"] in {"connected", "common-only"}
    target = entry.get("canonical_write_target")
    scopes = entry["read_scopes"]
    for scope in [*scopes, *entry["manual_read_bindings"]]:
        relative = safe_relative(scope["path"])
        try:
            (root / relative).resolve().relative_to(root.resolve())
        except (OSError, ValueError) as error:
            raise ContextError("read scope escapes knowledge root") from error
    namespace = target or (scopes[0]["path"] if scopes else None)
    return {**base, "project": entry, "registry_schema_version": 2,
            "knowledge_contract_path": str(root / ".system/knowledge-contract.json") if knowledge_contract(root) else None,
            "mode": "wiki-bounded" if active and scopes else "repo-only",
            "reason": "scoped project knowledge" if active and scopes else "no allowed read scope",
            "canonical_write_target": str(root / target) if target else None,
            "namespace_path": str(root / namespace) if namespace else None,
            "index_path": str(root / namespace / "index.md") if namespace else None}


def scoped_document(path: Path, root: Path, scope: dict, today: dt.date, *, manual: bool = False, allowed_parents: list[Path] | None = None) -> tuple[bool, str, dict, str]:
    try:
        actual = path.resolve(strict=True)
        relative = actual.relative_to(root.resolve())
        expected_root = root / ("my-wiki" if manual else "sys-wiki")
        actual.relative_to(expected_root.resolve(strict=True))
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            return False, "excluded corpus", {}, ""
        if manual:
            if actual != (root / scope["path"]).resolve():
                return False, "unbound manual note", {}, ""
        elif path.is_symlink() or actual.parent not in {parent.resolve() for parent in (allowed_parents or [root / scope["path"]])}:
            return False, "path escapes declared scope or is a symlink", {}, ""
        if not actual.is_file():
            return False, "not a regular document", {}, ""
        # No unbounded reads from a malformed/generated giant file.
        if actual.stat().st_size > 2_000_000:
            return False, "document exceeds scan budget", {}, ""
        metadata, body = parse_frontmatter(actual)
        lines = actual.read_text(encoding="utf-8").splitlines()
        keys = []
        for line in lines[1:]:
            if line.strip() == "---":
                break
            match = FRONTMATTER_KEY.match(line)
            if match:
                keys.append(match[1])
        if len(keys) != len(set(keys)):
            return False, "duplicate metadata keys", {}, ""
    except (OSError, ValueError, UnicodeError):
        return False, "path escapes or unreadable", {}, ""
    required = ("id", "title", "security_domain", "review_by", "status")
    if any(not metadata.get(key) for key in required):
        return False, "missing required metadata", metadata, body
    if metadata["security_domain"] != scope["security_domain"] or metadata.get("customer_scope") != scope["customer_scope"]:
        return False, "document security/customer scope mismatch", metadata, body
    if manual:
        if metadata["id"] != scope["id"]:
            return False, "manual id mismatch", metadata, body
        if metadata["status"] not in {"canonical", "provisional", "draft"}:
            return False, "manual status excluded", metadata, body
    else:
        if metadata.get("schema_version") != "2" or any(not metadata.get(k) for k in ("owner", "type", "verified_at")):
            return False, "invalid canonical schema", metadata, body
        if not re.fullmatch(r"KB-[A-Z0-9][A-Z0-9_-]*", metadata["id"]):
            return False, "invalid canonical stable id", metadata, body
        if metadata["type"] not in {"profile", "preference", "charter", "governance", "environment", "workflow", "reference", "business", "domain", "channel", "system", "decision", "delivery", "runbook"} or "related" not in metadata:
            return False, "invalid canonical type/relations", metadata, body
        if not frontmatter_list(path, "source_refs"):
            return False, "canonical source refs missing", metadata, body
        if metadata["status"] != "canonical":
            return False, f"status:{metadata['status']}", metadata, body
    try:
        review = dt.date.fromisoformat(metadata["review_by"])
        verified = dt.date.fromisoformat(metadata.get("verified_at", today.isoformat()))
        if verified > today or verified > review:
            return False, "invalid verification date", metadata, body
    except ValueError:
        return False, "invalid review/verification date", metadata, body
    if review < today:
        return False, f"overdue:{review}", metadata, body
    return True, "explicit-manual-read" if manual else "canonical-current", metadata, body


def bounded_metadata_list(path: Path, key: str, maximum: int) -> list[str]:
    """Read the supported flat YAML list without silently accepting malformed values."""
    lines = path.read_text(encoding="utf-8").splitlines()
    value, block = None, []
    active = False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = FRONTMATTER_KEY.match(line)
        if match:
            active = match[1] == key
            if active:
                value = match[2]
            continue
        if active and line.strip():
            item = re.fullmatch(r"  - (.+)", line)
            if not item:
                raise ValueError(f"invalid metadata list:{key}")
            block.append(item[1])
    if value is None:
        return []
    if value:
        try:
            items = json.loads(value)
        except ValueError:
            raise ValueError(f"invalid metadata list:{key}") from None
        if block:
            raise ValueError(f"invalid metadata list:{key}")
    else:
        items = []
        for item in block:
            item = item.strip()
            if item in {"[]", "{}", "null", "true", "false"} or item.startswith(('"', "[")):
                try:
                    item = json.loads(item)
                except ValueError:
                    raise ValueError(f"invalid metadata list:{key}") from None
            elif item.startswith("'") and item.endswith("'"):
                item = item[1:-1].replace("''", "'")
            elif item.isdigit():
                item = int(item)
            items.append(item)
    if (not isinstance(items, list) or len(items) > maximum
            or any(not isinstance(item, str) or not item.strip() or len(item) > 80
                   or any(ord(char) < 32 for char in item) for item in items)
            or len({item.strip().casefold() for item in items}) != len(items)):
        raise ValueError(f"invalid metadata list:{key}")
    return items


def phrase_matches(phrase: str, text: str) -> bool:
    """Whole phrases tolerate Korean spacing and common postpositions, not substrings."""
    phrase = " ".join(phrase.lower().split())
    if not phrase:
        return False
    compact = phrase.replace(" ", "")
    if re.fullmatch(r"[가-힣]{4,80}", compact):
        pattern = r"\s*".join(map(re.escape, compact))
        suffix = r"(?:에서는|으로|에서|부터|까지|은|는|이|가|을|를|에|의|로|과|와|도|만)?"
    else:
        pattern = r"\s+".join(re.escape(part) for part in phrase.split())
        suffix = ""
    return bool(re.search(r"(?<![\w])" + pattern + suffix + r"(?![\w])", text.lower()))


def matched_search_phrases(values: list[str], query: str) -> list[str]:
    matches, seen = [], set()
    for value in values:
        normalized = " ".join(value.casefold().split())
        compact = normalized.replace(" ", "")
        key = compact if re.fullmatch(r"[가-힣]{4,80}", compact) else normalized
        if key not in seen and phrase_matches(value, query):
            matches.append(value)
            seen.add(key)
    return matches


def spacing_terms(query: str) -> list[str]:
    """At most sixteen short Korean phrase candidates, never arbitrary substrings."""
    words = list(re.finditer(r"[가-힣]+", query[:2000]))[:24]
    result = []
    for width in (1, 2, 3):
        for index in range(len(words) - width + 1):
            group = words[index:index + width]
            if any(query[a.end():b.start()].strip() for a, b in zip(group, group[1:])):
                continue
            phrase = "".join(word[0] for word in group)
            if 4 <= len(phrase) <= 24 and phrase not in result:
                result.append(phrase)
                if len(result) == 16:
                    return result
    return result


def section_ranges(path: Path, query: str, *, limit: int, fallback: bool = False) -> list[dict]:
    """Rank sections across the complete file; return actual line ranges and byte cost."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    query_tokens = tokens(query)
    starts = [i for i, line in enumerate(lines) if re.match(r"^#{1,6} ", line)]
    body_start = 0
    if lines and lines[0].strip() == "---":
        body_start = next((i + 1 for i in range(1, len(lines)) if lines[i].strip() == "---"), len(lines))
    starts = sorted(set([body_start, *(i for i in starts if i >= body_start), len(lines)]))
    spacing = spacing_terms(query)
    ranked = []
    for start, end in zip(starts, starts[1:]):
        # Split huge individual sections into small line windows, not just first 12k.
        cursor = start
        while cursor < end:
            stop, size = cursor, 0
            while stop < end and size + len(lines[stop].encode("utf-8")) <= limit:
                size += len(lines[stop].encode("utf-8"))
                stop += 1
            if stop == cursor:
                cursor += 1  # one oversized line cannot fit a line-bounded read
                continue
            window = "".join(lines[cursor:stop])
            overlap = sorted(query_tokens & tokens(window))
            phrases = [term for term in spacing if phrase_matches(term, window)]
            if overlap or phrases or fallback:
                ranked.append({"line_start": cursor + 1, "line_end": stop, "bytes": size,
                               "matched_terms": overlap[:12], "score": len(overlap) * 10 + len(phrases) * 10})
            cursor = stop
    return sorted(ranked, key=lambda row: (-row["score"], row["line_start"] if fallback else row["bytes"], row["line_start"]))


def routed_v2(resolved: dict, query: str) -> dict:
    if resolved.get("mode") != "wiki-bounded":
        return {**resolved, "documents": [], "route_reason": resolved.get("reason", "repo-only")}
    root = Path(resolved["wiki_root"])
    entry = resolved["project"]
    policy = entry["retrieval"]
    max_documents = policy.get("max_documents", 4)
    max_bytes = policy.get("max_total_bytes", 80000)
    section_limit = min(12000, max_bytes)
    intents, intent_documents = matched_intents(policy, query)
    today = dt.date.today()
    contract = knowledge_contract(root)
    rejected, ranked, eligible, id_paths = [], [], {}, {}
    spacing = spacing_terms(query)
    scopes = [(s, False) for s in entry["read_scopes"]] + [(s, True) for s in entry["manual_read_bindings"]]
    seen = set()
    for scope, manual in scopes:
        try:
            parents = [] if manual else scoped_directories(root, scope, contract)
        except (ValueError, OSError) as error:
            raise ContextError(f"invalid scoped directories: {error}") from error
        paths = [root / scope["path"]] if manual else sorted(path for parent in parents for path in parent.glob("*.md"))
        for path in paths:
            if path in seen:
                continue
            seen.add(path)
            rel = path.relative_to(root).as_posix()
            if path.name == "index.md" and not manual:
                # Indexes are navigation, never semantic evidence or injected context.
                continue
            ok, reason, metadata, body = scoped_document(path, root, scope, today, manual=manual, allowed_parents=parents)
            if metadata.get("id"):
                id_paths.setdefault(metadata["id"], set()).add(rel)
            if not ok:
                rejected.append({"path": rel, "reason": reason})
                continue
            source = source_reference_health(path, resolved)
            if source["missing_commits"] or source["missing_paths"]:
                rejected.append({"path": rel, "reason": "invalid-source-ref"})
                continue
            document = {"path": str(path), "relative_path": rel, "id": metadata["id"], "title": metadata["title"],
                        "status": metadata["status"], "source_health": source, "read_only": True,
                        "corpus": "manual" if manual else "canonical", "scope": scope["customer_scope"]}
            try:
                aliases = bounded_metadata_list(path, "aliases", 8)
                tags = bounded_metadata_list(path, "tags", 8)
                related = bounded_metadata_list(path, "related", 6) if not manual else []
                if any(not re.fullmatch(r"KB-[A-Z0-9][A-Z0-9_-]*", item) or item == metadata["id"] for item in related):
                    raise ValueError("invalid canonical relations")
            except ValueError as exc:
                rejected.append({"path": rel, "reason": str(exc)})
                continue
            overlap = sorted(tokens(query) & tokens(f"{metadata['title']} {body} {path.name}"))
            phrases = [term for term in spacing if phrase_matches(term, f"{metadata['title']} {body}")]
            alias_matches = matched_search_phrases(aliases, query)
            tag_matches = matched_search_phrases(tags, query)
            intent = path.name in intent_documents or rel in intent_documents
            if not manual:
                intent = intent or path.relative_to(root / scope["path"]).as_posix() in intent_documents
            score = len(overlap) * 10 + min(2, len(phrases)) * 10 + (30 if intent else 0)
            score += min(2, len(alias_matches)) * 30 + min(2, len(tag_matches)) * 20
            reasons = (["query-overlap"] if overlap else []) + (["spacing-phrase"] if phrases else [])
            reasons += (["alias-match"] if alias_matches else []) + (["tag-match"] if tag_matches else []) + (["intent-route"] if intent else [])
            document.update(bytes=path.stat().st_size, score=score, matched_terms=overlap[:12],
                            matched_aliases=alias_matches, matched_tags=tag_matches, matched_phrases=phrases,
                            selection_reasons=reasons)
            eligible[rel] = {"document": document, "related": related}
            if score:
                ranked.append(document)
    duplicate_ids = {key for key, paths in id_paths.items() if len(paths) > 1}
    for rel, item in list(eligible.items()):
        if item["document"]["id"] in duplicate_ids:
            rejected.append({"path": rel, "reason": "duplicate canonical/manual id"})
            del eligible[rel]
    ranked = [document for document in ranked if document["relative_path"] in eligible]
    # Bare indexes provide navigation without pretending they are verified knowledge.
    index_path = Path(resolved["index_path"])
    try:
        index_path.resolve(strict=True).relative_to(root.resolve())
        if not index_path.is_file() or index_path.resolve().parent != index_path.parent.resolve():
            raise ValueError("index escapes scope")
    except (OSError, ValueError):
        return {**resolved, "mode": "repo-only", "documents": [], "rejected": rejected,
                "route_reason": "scoped navigation index missing or escaped"}
    navigation = {"path": str(index_path), "navigation_only": True, "follow_links": False,
                  "injected": False}
    selected, used = [], 0

    def select(document: dict) -> bool:
        nonlocal used
        if len(selected) >= max_documents:
            return False
        document = dict(document)
        remaining = max_bytes - used
        if remaining <= 0:
            return False
        if document["bytes"] <= min(section_limit, remaining):
            document["read_mode"] = "document"
        else:
            path = Path(document["path"])
            ranges = section_ranges(path, query, limit=min(section_limit, remaining))
            if not ranges:
                ranges = section_ranges(path, document["title"], limit=min(section_limit, remaining), fallback=True)
            chosen = []
            for row in ranges:
                if row["bytes"] <= remaining:
                    chosen.append(row)
                    remaining -= row["bytes"]
                    if len(chosen) == 3:
                        break
            if not chosen:
                rejected.append({"path": document["relative_path"], "reason": "no matching section fits budget"})
                return False
            document["read_mode"] = "sections"
            document["sections"] = sorted(chosen, key=lambda row: row["line_start"])
            document["bytes"] = sum(row["bytes"] for row in chosen)
        used += document["bytes"]
        selected.append(document)
        return True

    for document in sorted(ranked, key=lambda d: (-d["score"], d["bytes"], d["relative_path"])):
        select(document)
    # Direct evidence always gets first use of the budget. Never recurse or follow paths.
    by_id = {item["document"]["id"]: item["document"] for item in eligible.values()
             if item["document"]["corpus"] == "canonical"}
    seeds = list(selected)
    selected_ids = {document["id"] for document in selected}
    added = False
    for seed in seeds:
        if seed["corpus"] != "canonical" or added or len(selected) >= max_documents:
            continue
        for target_id in eligible[seed["relative_path"]]["related"]:
            target = by_id.get(target_id)
            if not target or target_id in selected_ids:
                continue
            if target["scope"] != seed["scope"] and not (seed["scope"] != "common" and target["scope"] == "common"):
                continue
            supplemental = {**target, "score": 0, "selection_reasons": ["related-one-hop"],
                            "related_via": {"id": seed["id"], "relative_path": seed["relative_path"], "relation": target_id}}
            if select(supplemental):
                added = True
                break
    return {**resolved, "index_document": None, "navigation": navigation, "query_documents": selected, "documents": selected,
            "index_counts_toward_document_limit": False, "query": query, "matched_intents": intents,
            "selected_bytes": used, "rejected": rejected,
            "route_reason": "bounded scoped retrieval" if selected else "no relevant current document; use repository context",
            "knowledge_health": {"status": "degraded" if rejected else "healthy", "rejected_count": len(rejected)}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiki-root", help="override the context-registry root")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("resolve", "doctor", "hook"):
        child = subparsers.add_parser(command)
        child.add_argument("--project", default=".")
    route_parser = subparsers.add_parser("route")
    route_parser.add_argument("--project", default=".")
    route_parser.add_argument("--query", required=True)
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--workspace", default=str(Path.home() / "projects"))
    args = parser.parse_args()
    try:
        if args.command == "resolve":
            value = resolve(Path(args.project), args.wiki_root)
        elif args.command == "route":
            value = routed_documents(resolve(Path(args.project), args.wiki_root), args.query)
        elif args.command == "doctor":
            value = doctor(Path(args.project), args.wiki_root)
        elif args.command == "hook":
            value = compact_hook(resolve(Path(args.project), args.wiki_root))
        else:
            value = audit_workspace(Path(args.workspace), args.wiki_root)
        print_result(value, args.compact)
        if isinstance(value, dict) and args.command == "doctor" and not value.get("healthy"):
            return 1
        if isinstance(value, dict) and args.command == "audit" and value.get("unclassified_count"):
            return 1
        return 0
    except ContextError as error:
        fallback = {
            "error": str(error),
            "mode": "repo-only",
            "managed": False,
            "documents": [],
            "healthy": False,
            "status": "unhealthy",
            "knowledge_health": None,
        }
        if args.command == "hook":
            return 0
        if args.command in {"resolve", "route"}:
            print_result(fallback, args.compact)
            return 0
        print(json.dumps(fallback, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
