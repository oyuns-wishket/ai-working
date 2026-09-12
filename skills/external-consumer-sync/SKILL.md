---
name: external-consumer-sync
description: Keep an application and an external bot, MCP server, SDK, or automation consumer compatible when shared schemas, business rules, events, or API contracts change. Use when one product change can silently break a separately deployed consumer.
---

# External consumer sync

Treat the producer and every external consumer as one compatibility unit while preserving their separate repositories and deployment permissions.

## Discover the contract

Read the producer's current schema, migrations, API/event types, and tests. Discover consumers from project documentation or a machine-local registry; do not guess repository names or scan unrelated directories. Record:

- changed fields, enums, identifiers, defaults, and lifecycle states;
- consumers that parse, cache, expose, or derive those values;
- compatibility direction and deployment order;
- credentials and environments owned by each project.

Customer names, repository locations, endpoints, and credentials belong in project-owned instructions or machine-local configuration, never in this public skill.

## Change as one unit

1. Add compatibility at the boundary before removing old behavior.
2. Update each consumer's parser, tool schema, prompts/docs, fixtures, and contract tests.
3. Use additive migrations and tolerant readers when deployments cannot be atomic.
4. Verify old and new payloads where a transition window exists.
5. Deploy in the measured order defined by the involved projects. A request to change one repository does not authorize writes or deployment in another.

Finish only after the producer contract and every in-scope consumer pass their own validation, or list the consumer that remains blocked and the compatibility bridge left in place.
