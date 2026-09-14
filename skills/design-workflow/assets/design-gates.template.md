# Design gate evidence

Use this section inside the task implementation note. Do not mark a gate complete from model inference, a subagent decision, or a user message sent before the listed options or artifacts were shown.

## Mode and lock

- Mode: `new | rebrand | refactor | small-feature | audit`
- Application source writes: `locked | unlocked`
- Primary purpose and scope:
- Existing user request/approval and design source:
- Required gate set: full (new/rebrand/world replacement/full representative-screen replacement) | scoped (small-feature/preserving refactor) | none (audit)

For scoped work, mark the four new-design sections below `N/A` with a reason and record confirmed scope, relevant UI states, acceptance criteria, and existing design authority here. Do not demand new product answers or three comps for a preserved small feature. A visual-world or full representative-screen replacement requires the full gate set. Audit remains locked and does not create this file.

- Scoped acceptance evidence:

## Product interview

- [ ] A real user answer or explicit summary approval was received
- Question:
- User answer:
- Confirmed user, job, differentiation, success and failure criteria:

## Design-direction interview

- [ ] Brand traits, reference/anti-reference, density, platform and accessibility were confirmed
- Question:
- User answer:

## Visual-world decision

- [ ] Three distinct worlds were shown
- Options:
- User choice, or explicit delegation after viewing:

## High-fidelity comps

- [ ] Exactly three comps inside the selected world were shown together
- Comp paths or URLs:
- User decision: `approve | combine | revise | reject`
- User answer:
- Adopt:
- Reject:

## Implementation unlock

- [ ] Every gate required for the selected mode is complete; any N/A has a valid scoped-work reason
- Implementation unlocked: `yes | no`
