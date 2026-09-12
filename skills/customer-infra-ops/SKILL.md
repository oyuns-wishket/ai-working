---
name: customer-infra-ops
description: Discover, diagnose, and change customer-owned cloud, database, DNS, CI, and deployment infrastructure using only the current project's documented accounts and secret sources. Use for infrastructure operations where environment identity and ownership must be verified before mutation.
---

# Customer infrastructure operations

Start from the current project's instructions and live provider identity. Never import another customer's topology, credentials, account profile, hostnames, or defaults.

## Safe discovery

1. Read repository infrastructure docs, deployment configuration, migrations, and CI workflows.
2. Identify provider, account/project, region, environment, domain, and credential source without printing secrets.
3. Verify the authenticated identity with the provider's read-only identity command.
4. Build a current topology from read-only APIs. Treat documentation as intent and live evidence as runtime truth.
5. Stop if the authenticated tenant or environment differs from the project-owned configuration.

Store reusable generic procedure here. Store customer topology and approved resource identifiers in that customer's repository or machine-local config.

## Changes

Prepare an exact plan with target environment, resources, diff, rollback, and verification. Run provider-native preview or dry-run where available. Existing authorization applies only to the described environment and resources; request a decision for destructive data loss, unexpected resources, or a new production scope.

After applying, verify provider state, application health, logs, DNS resolution, and deployment revision as relevant. Redact account numbers, endpoints containing credentials, tokens, and connection strings from output.
