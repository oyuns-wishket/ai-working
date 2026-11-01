# Organization scope and durable transport recovery

## Goal and authorization
The user asked to update the reusable bot development skill as organization-wide development and attachment support were implemented. Existing publication authorization applies; no customer identifiers or secrets are included here.

## Changes and rationale
- Preserve organization-wide repository scope; distinguish catalog, source and publication access, and pin each task to a source revision.
- Preserve attachment bytes during backup and audit actual reads rather than tool calls alone.
- Recover committed chat requests without redownloading deleted originals; recheck ACLs for all delivery paths and stop active plus queued work.
- Cover process registration and late adoption races with bounded cleanup and fail-stop. Distinguish tested OS behavior.

These additions capture verified failure patterns and do not prescribe a particular customer's infrastructure. A single practice repository and an implicit permission expansion of an existing investigation bot were rejected because they change scope or authority.

## Verification
Skill validation passed (25 skills); public history audit passed. Bootstrap/status resolves both agents to the same canonical skill directories (78 checks). Node hook/bootstrap suite:81 passed,1 existing resource-guard fixture failure (mock cwd expected but observed unknown); no hook implementation changed. GitHub public-safety result is checked after push.

## Deviations and follow-up
No new skill entrypoint or bootstrap layout change. Real employee usability and modality support must still be measured by each consuming project.
