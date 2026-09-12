# `<channel>` integration workbook

> Copy this file into the target repository. Mark every claim as `docs`, `fake`, `live-read`, or `live-write` evidence.

## Metadata

- Channel/internal code:
- Seller/store identifier (record secret location, never the value):
- Issue/branch/PR:
- Official docs URL/version/checked date:
- Admin UI timezone/as-of:
- Readiness: research / code / live-read / live-write / production

## API, auth, and limits

| Topic | Finding | Evidence | Open question |
| --- | --- | --- | --- |
| Auth/token rotation | | | |
| OAuth/user GUI action | | | |
| IP allowlist | | | |
| Rate limit/retry | | | |
| Max window/pagination/batch | | | |
| Timezone/date boundaries | | | |

## Natural keys

| ERP field | Raw field | Level and meaning | Stability evidence |
| --- | --- | --- | --- |
| order key | | | |
| shipment/group key | | | |
| line key | | | |
| claim key | | | |

## Raw status mapping

| Raw status + helper field/endpoint | Admin label | Normalized status | Live sample | Unknown handling |
| --- | --- | --- | --- | --- |
| | | `PAID` | | |
| | | `PREPARING` | | |
| | | `SHIPPING` | | |
| | | `DELIVERED` | | |
| | | `CANCELLED` | | |
| | | `UNKNOWN` | | |

## Collection and reconcile

| Path | Query basis | Schedule/trigger | Purpose | Missed-transition backstop |
| --- | --- | --- | --- | --- |
| Incremental | | | | |
| On-demand | | | | |
| Periodic backstop | | | | |
| Terminal reconcile | | | | |

## Dashboard reconciliation

| Metric | Admin count | API query/count | ERP query/count | Scope/as-of | Difference |
| --- | --- | --- | --- | --- | --- |
| Paid | | | | | |
| Preparing | | | | | |
| Shipping | | | | | |
| Delivered | | | | | |
| Cancel/return/exchange | | | | | |
| Unanswered inquiry | | | | | |

## Write transition map

| Transition | Eligible raw state | Endpoint/method | Request key/batch | User impact | Refetch proof |
| --- | --- | --- | --- | --- | --- |
| Paid → preparing | | | | | |
| Invoice/dispatch | | | | | |

## Terminal policy

| Candidate | Explicit API evidence | Planned update | No-evidence behavior |
| --- | --- | --- | --- |
| Missing from current list | | | Preserve + unresolved |
| Claim response | | | |
| Partial quantity mismatch | | | Preserve + future claim model |

## Live probe and dry-run

- Server/fixed IP/as-of:
- Read-only query and counts:
- Admin/API difference:
- Dry-run candidate/confirmed/unresolved/error:
- Idempotent rerun result:
- Write approver and canary:

## Tests, deploy, and E2E

- [ ] Auth/parser/rate-limit tests
- [ ] Normalize/key/idempotency/state-regression tests
- [ ] Queue/retry/reaper/terminal UI tests
- [ ] Dashboard scope/filter/card navigation tests
- [ ] Runtime import path, cron, logs, environment checked
- [ ] Admin UI ↔ API ↔ DB ↔ ERP final reconciliation

## Failures returned to the guide

| Symptom | Root cause | Fix | New reusable guardrail |
| --- | --- | --- | --- |
| | | | |

## Future scope

- Detailed cancel/return/exchange model and APIs:
- Inquiry/review:
- Settlement/promotion:
- Unresolved data-model constraints:
