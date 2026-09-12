# Private SSOT retirement ledger

This ledger accounts for all 209 files tracked by the former private repository without importing its Git history.
The public repository keeps a fresh history so deleted credentials, personal infrastructure, customer material, and
session artifacts cannot become reachable public blobs.

| Former source | Files | Disposition |
|---|---:|---|
| Root/bootstrap/manifest | 5 | Public-only bootstrap and documentation rewritten in `ai-working`; obsolete overlay metadata dropped |
| Global configuration | 5 | Tool-neutral policy and hook manifests rewritten publicly; machine-specific settings excluded |
| Skills: 23 reusable skill directories | 120 | Current behavior ported or generalized under `skills/`; caches excluded |
| Skills: customer-specific sync and infrastructure | 5 | Rewritten as `external-consumer-sync` and `customer-infra-ops`; customer topology stays in its owning project |
| Skills: workplace calendar | 1 | Rewritten to load channel and mention IDs from machine-local configuration |
| Skills: external knowledge-wiki symlink | 1 | Symlink rejected; clean-room public workflow replaces it |
| Templates | 6 | Generic templates retained; project-specific values removed |
| Hook tests | 3 | Ported with customer and legacy names removed |
| Workspace defaults | 2 | Generic workspace policy retained; customer/project registry data removed |
| Implementation/history docs | 28 | Classified as historical evidence; only reusable architecture and current migration decisions are distilled publicly |
| Personal/customer memory | 27 | Never published; current local memory is detached into a machine-local directory during migration |
| OMC/session/cache state | 6 | Ephemeral runtime state; excluded from source control |
| **Total** | **209** | Every tracked path has a destination or an explicit exclusion boundary |

The former private working tree and its dirty worktree are preserved as read-only migration evidence until the public
cutover passes. They are not an SSOT and must not be linked by Claude, Codex, hooks, workspace files, or local config.
