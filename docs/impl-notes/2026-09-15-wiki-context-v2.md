# Wiki context v2

## Gate evidence

The user approved the previously discussed wiki transition and the shared retrieval/closeout updates. This change implements public, reusable contract discovery, scoped reads, and canonical-only write discovery. Private registry values and wiki content stay outside this repository. Implementation occurs in an isolated checkout; runtime activation is owned by the coordinating task.

## Scope and verification

Preserve v1 compatibility while accepting a v2 registry with separate read scopes, canonical write targets, and exact opt-in manual note bindings. Merge default retrieval policy; reject cross-customer, stale, unclassified and escaped content. Common knowledge reads are nonrecursive. Return bounded section ranges so relevant late sections of long notes can be read without loading the entire note. Test v1 regressions, v2 boundaries and closeout discovery.

## Validation

- Existing and v2 resolver: 24 tests passed.
- Known closeout discovery/publication: 25 tests passed.
- Hook/bootstrap Node suite: 34 tests passed.
- Public audit including history and skill validation passed.
- Runtime activation and installed-link verification are performed by the coordinating task after integration; this checkout does not alter the live adapter.
