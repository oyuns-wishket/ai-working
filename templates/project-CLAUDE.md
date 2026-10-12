# <repo> — project guide

## Stack & commands
- Stack: <next16/react19/ts/tailwind4/shadcn, supabase, vercel — fill from package.json>
- Install/dev/build/lint/test: <exact commands; follow lockfile (npm/pnpm)>
- Completion = build + lint (+ test) pass, verified.

## Skill routing
- 기획·명세 → generate-spec · 구현 → dev-protocol · 브랜치 개발 → feature-flow.

## Rules
<!-- This file is the single body for Claude and Codex: save it as AGENTS.md and make CLAUDE.md `@AGENTS.md`. -->
- Always-on rules go here (branching/sandbox, common-code/ERP domain). No `@path` imports.
- Path-scoped or very large rules stay in `.claude/rules/`; list each: `- .claude/rules/<x>.md — read when touching <paths>.`

## Infra
- Summary here; details in `docs/infra.md` (how dev/deploy/branches work).

## Domain
- ERP domain model lives in `docs/erp-domain/*.md` — keep updated as model/requirements change.
