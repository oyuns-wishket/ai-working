# Project audit

## Read order

1. Repository rules: `CLAUDE.md`, `AGENTS.md`, nested rules
2. Current task history: impl-notes, HANDOFF, linked issue/spec
3. Product context: product brief, requirements, user flows
4. Design context: `PRODUCT.md`, `DESIGN.md`, design-system docs, tokens
5. Implementation: app shell, navigation, shared UI, page under change
6. Runtime evidence: representative URLs, screenshots, console/network logs

## Static inventory

Record:

- framework and version
- package manager from lockfile
- CSS system: Tailwind, CSS modules, styled components, vanilla CSS, native
- component library and icon system
- fonts and loading method
- theme/color/token definitions
- breakpoints and layout containers
- navigation model
- existing visual tests, Storybook, Playwright
- build, lint, test, dev commands

Use `rg` and project manifests. Do not infer the stack from the workspace default.

## Visual inventory

Capture at least:

- global shell/header/sidebar
- one dense screen
- one form or detail screen
- the exact target screen
- desktop viewport
- mobile viewport when responsive behavior is in scope

For a small feature, inspect the target plus up to two available adjacent patterns. Do not invent missing screens. For rebrand/refactor, inspect representative flows rather than every route. For a new product, record that there is no existing UI baseline.

Follow one relevant user task end to end. Note where the user must guess, wait without feedback, repeat input, or recover from errors. Select a primary purpose through [experience-routing.md](experience-routing.md); keep specialist inspection bounded to that purpose.

## Runtime evidence

- browser console errors and warnings
- failed network requests
- horizontal overflow
- clipped/folded content
- keyboard order and focus visibility
- loading, empty, error, disabled, success states
- layout shifts and reduced-motion behavior

Do not confuse an existing runtime bug with a design regression. Record baseline issues before editing.

## Audit output

Use `assets/design-audit.template.md` when a durable report is useful. Classify every item:

In read-only audit mode, report in conversation unless the user requested a saved report. Use already available detectors only; do not install tools or create project configuration. Missing tooling is a coverage limitation, not permission to mutate the project.

- `observed`: directly seen in source or browser
- `detector`: produced by Impeccable
- `inferred`: likely consequence requiring confirmation

Prioritize by user impact:

- P0: task impossible, content unreadable, security/data risk
- P1: core flow materially obstructed
- P2: inconsistent hierarchy, responsive or accessibility defect
- P3: polish and optional refinement

For each finding include evidence, affected scope, recommended correction, and regression risk.
