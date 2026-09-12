#!/usr/bin/env python3
"""Inspect a project and recommend reusable worker capabilities."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Optional

from configure import default_config_path, load_config

PRUNED_DIRS = {
    ".git",
    ".next",
    ".turbo",
    ".vercel",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "vendor",
}

CAPABILITY_ALIASES = {
    "project-mapper": {"explore", "explorer", "pm", "project-analyst", "code-mapper"},
    "erp-domain-analyst": {
        "erp-domain-analyst",
        "business-analyst",
        "domain-reviewer",
        "pm",
    },
    "implementation-worker": {
        "developer",
        "executor",
        "worker",
        "backend-developer",
        "frontend-developer",
    },
    "test-engineer": {"tester", "test-engineer", "qa-tester"},
    "reviewer": {"reviewer", "code-reviewer", "domain-reviewer"},
    "verifier": {"verifier", "qa-tester", "reviewer"},
    "db-guardian": {
        "db-guardian",
        "postgres-pro",
        "db-migration",
        "supabase-migrator",
    },
    "ui-designer": {"designer", "ui-designer", "ux-auditor", "frontend-designer"},
    "integration-specialist": {
        "integration-specialist",
        "channel-specialist",
        "api-specialist",
    },
    "security-auditor": {"security-auditor", "security-reviewer"},
    "data-reconciler": {"data-reconciler", "migration-specialist"},
    "performance-auditor": {
        "performance-auditor",
        "performance-engineer",
    },
}


def git_root(project: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"Not a Git project: {project}\n{result.stderr.strip()}")
    return Path(result.stdout.strip()).resolve()


def read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def collect_paths(root: Path, limit: int = 12000) -> list[str]:
    paths: list[str] = []
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in PRUNED_DIRS]
        current_path = Path(current)
        for name in files:
            try:
                paths.append(str((current_path / name).relative_to(root)))
            except ValueError:
                continue
            if len(paths) >= limit:
                return paths
    return paths


def parse_claude_agent(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter: dict[str, str] = {}
    if text.startswith("---\n"):
        _, block, *_ = text.split("---", 2)
        for line in block.splitlines():
            if ":" in line and not line.startswith((" ", "\t", "-")):
                key, value = line.split(":", 1)
                frontmatter[key.strip()] = value.strip().strip("\"'")
    return {
        "name": frontmatter.get("name", path.stem),
        "description": frontmatter.get("description", ""),
        "source": "claude",
        "path": str(path),
        "text_sample": text[:4000],
    }


def parse_codex_agent(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
        data: dict[str, Any] = {}
        for line in text.splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, raw = line.split("=", 1)
            key = key.strip()
            raw = raw.strip()
            if key not in {"name", "description", "developer_instructions"}:
                continue
            try:
                data[key] = json.loads(raw)
            except json.JSONDecodeError:
                data[key] = raw.strip("\"'")
    except OSError:
        data = {}
    return {
        "name": data.get("name", path.stem),
        "description": data.get("description", ""),
        "source": "codex",
        "path": str(path),
        "text_sample": str(data.get("developer_instructions", ""))[:4000],
    }


def parse_canonical_agent(path: Path) -> dict[str, Any]:
    data = read_json(path)
    return {
        "name": data.get("name", path.stem),
        "description": data.get("description", ""),
        "capability": data.get("capability"),
        "source": "canonical",
        "path": str(path),
        "text_sample": str(data.get("instructions", ""))[:4000],
    }


def collect_agents(root: Path) -> list[dict[str, Any]]:
    agents: list[dict[str, Any]] = []
    claude_dir = root / ".claude" / "agents"
    codex_dir = root / ".codex" / "agents"
    canonical_dir = root / ".agents" / "multi-agent-dev" / "workers"
    if claude_dir.is_dir():
        agents.extend(
            parse_claude_agent(path) for path in sorted(claude_dir.glob("*.md"))
        )
    if codex_dir.is_dir():
        agents.extend(
            parse_codex_agent(path) for path in sorted(codex_dir.glob("*.toml"))
        )
    if canonical_dir.is_dir():
        agents.extend(
            parse_canonical_agent(path) for path in sorted(canonical_dir.glob("*.json"))
        )
    return agents


def package_manager(root: Path, package: dict[str, Any]) -> Optional[str]:
    declared = package.get("packageManager")
    if isinstance(declared, str) and declared:
        return declared
    candidates = [
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("bun.lockb", "bun"),
        ("bun.lock", "bun"),
        ("package-lock.json", "npm"),
    ]
    for filename, manager in candidates:
        if (root / filename).exists():
            return manager
    return None


def existing_candidates(
    capability: str, agents: list[dict[str, Any]]
) -> list[dict[str, str]]:
    aliases = CAPABILITY_ALIASES.get(capability, {capability})
    matches: list[dict[str, str]] = []
    for agent in agents:
        name = str(agent.get("name", "")).lower()
        capability_name = str(agent.get("capability", "")).lower()
        identity_text = " ".join(
            [
                name,
                capability_name,
                str(agent.get("description", "")).lower(),
            ]
        )
        boundary_match = any(
            re.search(
                rf"(^|[^a-z0-9]){re.escape(alias)}($|[^a-z0-9])",
                identity_text,
            )
            for alias in aliases
        )
        if capability_name == capability or name in aliases or boundary_match:
            matches.append(
                {
                    "name": str(agent.get("name", "")),
                    "source": str(agent.get("source", "")),
                    "path": str(agent.get("path", "")),
                }
            )
    return matches


def under_any_root(project: Path, roots: list[str]) -> Optional[bool]:
    if not roots:
        return None
    for root in roots:
        try:
            project.relative_to(Path(root).resolve())
            return True
        except ValueError:
            continue
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a project and recommend multi-agent capabilities."
    )
    parser.add_argument("--project", default=".")
    parser.add_argument("--config", default=str(default_config_path()))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = git_root(Path(args.project).expanduser())
    config_path = Path(args.config).expanduser()
    config = load_config(config_path)
    package = read_json(root / "package.json")
    path_list = collect_paths(root)
    path_index = "\n".join(path_list).lower()
    package_text = json.dumps(package, ensure_ascii=False).lower()
    combined = f"{path_index}\n{package_text}"
    dependencies = {
        **(package.get("dependencies") or {}),
        **(package.get("devDependencies") or {}),
    }

    signals = {
        "database": any(
            token in combined
            for token in (
                "supabase",
                "prisma",
                "migration",
                "postgres",
                "mysql",
                "mssql",
            )
        ),
        "ui": any(
            token in dependencies
            for token in ("react", "next", "vue", "flutter", "@angular/core")
        )
        or any(token in combined for token in ("design-system", "components/ui")),
        "security": any(
            token in combined
            for token in ("auth", "rls", "rbac", "permission", "organization")
        ),
        "integration": any(
            token in combined
            for token in (
                "odoo",
                "fm4",
                "더존",
                "oms",
                "webhook",
                "channel",
                "shipping",
                "marketplace",
            )
        ),
        "data_reconciliation": any(
            token in combined
            for token in (
                "xlsx",
                "excel",
                "import",
                "reconcile",
                "migration",
                "seed",
                "inventory",
                "settlement",
            )
        ),
        "performance": any(
            token in combined
            for token in (
                "virtual",
                "batch",
                "queue",
                "cron",
                "aggregate",
                "dashboard",
            )
        ),
    }

    core = [
        ("project-mapper", "map project rules, stack, modules, and verification"),
        ("erp-domain-analyst", "derive ERP invariants and acceptance criteria"),
        ("implementation-worker", "implement a bounded write task"),
        ("test-engineer", "write and run acceptance and regression tests"),
        ("reviewer", "independently review diffs and risks"),
        ("verifier", "remeasure completion with fresh command output"),
    ]
    conditional = [
        ("db-guardian", "database", "database/RLS/migration signals detected"),
        ("ui-designer", "ui", "UI framework or design-system signals detected"),
        (
            "integration-specialist",
            "integration",
            "external ERP/channel/API integration signals detected",
        ),
        (
            "security-auditor",
            "security",
            "authentication, RLS, RBAC, or organization scope detected",
        ),
        (
            "data-reconciler",
            "data_reconciliation",
            "migration/import/reconciliation signals detected",
        ),
        (
            "performance-auditor",
            "performance",
            "batch, queue, virtualized data, or dashboard signals detected",
        ),
    ]

    agents = collect_agents(root)
    recommendations: list[dict[str, Any]] = []
    for capability, reason in core:
        recommendations.append(
            {
                "capability": capability,
                "kind": "core",
                "reason": reason,
                "existing_candidates": existing_candidates(capability, agents),
            }
        )
    for capability, signal, reason in conditional:
        if signals[signal]:
            recommendations.append(
                {
                    "capability": capability,
                    "kind": "conditional",
                    "reason": reason,
                    "existing_candidates": existing_candidates(capability, agents),
                }
            )

    rules = [
        relative
        for relative in path_list
        if relative in {"CLAUDE.md", "AGENTS.md"}
        or relative.startswith(".claude/rules/")
    ]
    selected_scripts = {}
    for name, command in (package.get("scripts") or {}).items():
        if any(
            token in name
            for token in ("build", "lint", "test", "typecheck", "check", "db:")
        ):
            selected_scripts[name] = command

    payload = {
        "project": {
            "root": str(root),
            "name": root.name,
            "within_configured_workspace": under_any_root(
                root, config.get("workspace_roots", [])
            ),
            "package_manager": package_manager(root, package),
            "rules": sorted(rules),
            "verification_scripts": selected_scripts,
        },
        "config": {
            "path": str(config_path),
            "exists": config_path.exists(),
            "erp_domain_references": [
                value
                for value in config.get("erp_domain_references", [])
                if Path(value).is_file()
            ],
            "platforms": config.get("platforms", []),
            "worktree_root": config.get("worktree_root"),
        },
        "signals": signals,
        "existing_agents": [
            {key: value for key, value in agent.items() if key != "text_sample"}
            for agent in agents
        ],
        "recommended_capabilities": recommendations,
        "scan": {
            "file_count": len(path_list),
            "truncated": len(path_list) >= 12000,
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
