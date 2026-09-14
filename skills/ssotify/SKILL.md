---
name: ssotify
description: Create, improve, or consolidate reusable personal skills in the public ai-working SSOT. Use for skill authoring and workflow capture; skip project-only facts and ordinary task execution.
---

# Reusable skill authoring

Resolve `AI_WORKING_ROOT` from the current checkout or installed source link. Author shared skills only in `ai-working/skills/<name>/`; both agents receive links through bootstrap. Keep credentials, customer facts and machine-specific settings out of public instructions.

## Decide whether a skill is needed

Use the actual request and existing answers to establish the repeated task, intended trigger and useful outcome. Ask only about missing choices that materially change behavior. Do not repeat intake, type confirmation or research permission when the conversation already establishes them.

Inspect related skills and callers before adding an entrypoint. Extend the current owner for overlapping tasks; move conditional procedures into its references. A single project fact belongs in that project's documentation. Preserve rarely used operational capabilities unless their removal is requested or their role is clearly covered elsewhere.

## Write the minimum useful guidance

- Use `name` and a concise, discriminating `description`. Describe the capability and trigger, putting the main use case first. Avoid broad MUST-use catchalls and exhaustive keyword lists.
- Keep `SKILL.md` focused on decisions that the model would otherwise get wrong, required boundaries and the paths to relevant resources. Read references only when their mode applies; do not load the whole reference tree.
- Add scripts for repeated deterministic work; put output templates in assets. A short instruction-only skill needs no extra scaffolding. The [minimal template](assets/skill-template.md) is optional.
- Preserve current user scope, project rules and existing authorization. Do not turn examples into universal approval gates, fixed review counts or mandatory interviews. Important unresolved product choices and new destructive scope still need user input.
- Use native platform mechanisms and actual available tools. A plugin-only worker name is not a portable capability. Avoid a second global-rule source or a dependency chain for ordinary planning, execution and verification.
- For uncertain/versioned external behavior, verify current primary documentation and cite the supporting page. Clearly label anything not verified.

## Validate and apply

Run `python3 scripts/validate_skills.py` and `python3 scripts/public_audit.py --history` from the source repository. Run changed scripts and meaningful existing checks. For substantial behavioral instructions, examine realistic cases: intended trigger, nearby non-trigger, existing approval, missing information and failure recovery. Use an independent native evaluation when complexity justifies it and delegation is available; simple wording changes do not require a new test suite.

Review the final diff and dependency paths. When consolidating, map old capabilities to their new owner, update callers, and preserve external originals. Remove only reviewed owned links from installed catalogs; do not delete vendor caches or source directories. Local absolute paths and selected external sources stay in the machine-local registry.

Run bootstrap from the canonical checkout, verify both agents resolve the same whole directories, and update README for changed entrypoints. Reuse existing commit/push authorization for the same scope; ask once only if publication was not authorized. Report actual validation and any session reload requirement.
