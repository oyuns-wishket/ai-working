# Product and design context

## Source priority

1. User-confirmed brand/product requirements
2. Existing project `PRODUCT.md`, `DESIGN.md`, design-system docs
3. Existing production UI and reusable components
4. Referenced designs, decomposed into adopt/reject elements
5. Taste Skill or model-generated proposal

Never let a generic skill silently override an established project system.

## Minimum product questions

Ask only values that cannot be discovered:

- What job is the user completing?
- Who is the primary user and what is their expertise?
- Is this a brand/marketing surface or a product/work surface?
- What must a person understand or finish on this specific page? Which purpose in [experience-routing.md](experience-routing.md) matches it?
- Which current behavior or identity must remain?
- Which result would make the change unsuccessful?

For `new` or `rebrand`, also establish brand traits, references/anti-references, content density, platform priority, and accessibility target. Ask one decision at a time when the answer changes implementation.

For a new product with no `PRODUCT.md`, require at least one real user answer or explicit confirmation round even when repository evidence suggests plausible answers. “No design in mind” means the visual authority is open; it does not delegate product truth or visual-direction approval to the model.

Before implementation in `new` or `rebrand`, present three distinct visual worlds, let the user choose or explicitly delegate after seeing them, then render and show exactly three high-fidelity compositional comps inside the chosen world. Record the user’s `approve / combine / revise / reject` decision. A reviewer or subagent may critique but may not provide the approval.

## DESIGN.md contents

Use `assets/DESIGN.template.md`. Keep decisions concrete:

- named color tokens and usage, not a palette screenshot alone
- Korean and Latin font stack, weights, loading, fallback
- type ramp and line-height
- spacing, container, grid, density
- radius, border, elevation
- navigation and component patterns
- interaction states and motion
- page-task/brand motion recommendation, interactive choices or reused approved presets from [motion-design.md](motion-design.md)
- for charts, Bklit route or documented compatibility exception and same-data interaction choice
- for assisted 3D, agent-owned creation/edit/export route, actual model review and verified web delivery
- for external tools, sanitized free/included-paid capability evidence and delivery rights from [tool-capabilities.md](tool-capabilities.md); no personal account information
- responsive transformations
- accessibility constraints
- explicit anti-patterns
- small-feature scope guard when applicable
- selected experience purpose and tools, with reuse, compatibility, and fallback decisions
- observable task acceptance criteria, rather than invented satisfaction scores

## Web quality

Use [web-quality.md](web-quality.md) for alignment, typography, density, interaction feedback, responsive behavior, and performance. Preserve the existing scale and brand before proposing new values. Read only the selected purpose's specialist reference; these recommendations do not replace product or comp approval.

## Existing design-system migration

When an older document such as `docs/design-system/DESIGN-SYSTEM.md` exists:

1. Do not create a competing token source.
2. Map its tokens and decisions into `DESIGN.md`, or document `DESIGN.md` as a short index pointing to the existing canonical file.
3. Record contradictions before editing CSS.
4. Preserve stable token names unless rebranding explicitly authorizes migration.
5. Provide old → new token mapping and rollout order for renamed tokens.

## References

For each reference, record:

| Reference | Adopt | Reject | Reason |
|---|---|---|---|

Adopt relationships and principles, not copyrighted assets or a pixel-for-pixel copy.
