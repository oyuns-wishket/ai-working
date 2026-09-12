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
- responsive transformations
- accessibility constraints
- explicit anti-patterns
- small-feature scope guard when applicable

## Principles

- Use one dominant visual anchor per screen.
- Build hierarchy in this order: whitespace, weight, size, color, decoration.
- Keep body line-height around 1.4–1.6 and headings around 1.1–1.25 unless the font needs different metrics.
- Use no more than two intentional font families. Validate Korean glyph coverage and mixed-script rhythm.
- Maintain WCAG AA contrast by default: 4.5:1 for normal text, 3:1 for large text and relevant UI boundaries.
- Never communicate state by color alone.
- Use purpose-driven motion; provide reduced-motion behavior.
- Keep touch targets at least 44×44 CSS px where mobile interaction applies.
- Choose breakpoints based on content failure, not named devices alone.

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
