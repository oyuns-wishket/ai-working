# CLAUDE.md — project workspace root

This directory contains independent client, internal, and experimental projects. Each project owns its code, deployment, credentials, and project-specific rules.

## Starting work

- Read the target project's `CLAUDE.md`, `AGENTS.md`, and `.claude/rules/` before planning or editing.
- Current code, migrations, tests, and verified runtime evidence override cached notes.
- Use `project-wiki-context` before non-trivial work when the workspace has a local project-knowledge registry.
- Treat unavailable, stale, or contested knowledge as context gaps and continue from repository evidence where safe.

## Common defaults

- Converse in Korean. Keep code, commands, and technical terms in English.
- Detect the stack and package manager before running commands. Follow the existing lockfile and `packageManager` field.
- Keep credentials in project-owned secret stores or local environment files that the project documents. Never copy secrets into this workspace rule or the public `ai-working` repository.
- Inspect credential bootstrap scripts before executing them.
- Measure build, lint, and relevant tests before declaring code work complete.
- Project-specific rules override this workspace file.

## Project boundaries

- Keep each client or product in its own repository unless its own instructions define a monorepo.
- Put durable project decisions in that project's tracked documentation.
- Put reusable, project-neutral workflows in `ai-working/skills/<name>/SKILL.md`.
- Put reusable global agent rules in `ai-working/global/CLAUDE.md`.
- Put customer-specific facts, identifiers, credentials, and operational values only in the customer repository or its approved private system.
- Do not enumerate project names here; lists become stale and can expose private context.

## Shared ERP knowledge

- Read `~/aidp/erp-domain.md` before designing an ERP feature when that file is present.
- Promote only concepts that apply across projects.
- Keep customer-specific rules and figures in `<project>/docs/erp-domain/`.
- Resolve conflicts in favor of the project's current code and verified infrastructure.

## Standard project files

When present, follow:

- `<project>/.claude/rules/branching.md` for branch, database, and preview rules.
- `<project>/.claude/rules/erp.md` for ERP conventions.
- `<project>/docs/handoff/HANDOFF.md` for cross-machine handoff.
- `<project>/docs/infra.md` for deployment and infrastructure.
