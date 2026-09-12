# Online channel release checklist

## Scope and evidence

- [ ] Read repository rules, as-is sources, specs, implementation notes, and handoff.
- [ ] Fix seller, timezone, as-of, date range, state definitions, and order-vs-line counting.
- [ ] Record official API URL/version/checked date and evidence level.
- [ ] Preserve source keys, raw payload, timestamps, and audit data for future claims.

## Data contract

- [ ] Confirm order/shipment/line/claim natural keys.
- [ ] Map every raw state to `PAID / PREPARING / SHIPPING / DELIVERED / CANCELLED / UNKNOWN`.
- [ ] Confirm whether status is order-, item-, or shipment-level.
- [ ] Test idempotent reruns, late events, and state-regression protection.

## Collection and dashboard

- [ ] Live read-only probe succeeds from the production network path.
- [ ] Admin UI ↔ API ↔ DB ↔ ERP counts use the same scope.
- [ ] Incremental collection captures old-order state transitions or has a periodic backstop.
- [ ] Dashboard snapshot and order list share the same collection run/as-of.
- [ ] Dashboard cards open the matching ERP filters or a stable external admin page.

## Terminal safety

- [ ] Never mark terminal from absence alone.
- [ ] Require explicit single-order/claim/webhook evidence.
- [ ] Preserve ambiguous and partial-quantity cases as unresolved.
- [ ] Review dry-run candidate/confirmed/unresolved/error counts.
- [ ] Never physically delete; default-exclude cancelled and provide explicit audit filtering.

## Writes and queue UX

- [ ] Revalidate channel eligibility immediately before each write.
- [ ] Record per-request partial success, race, timeout, and 429 outcomes.
- [ ] Refetch source truth after accepted writes.
- [ ] Obtain user approval and start with one canary.
- [ ] Poll only while pending/processing; stop timer, polling, and spinner on done/failed.
- [ ] Base auto-refresh cooldown on terminal `processedAt`, not enqueue time.

## Deploy and closure

- [ ] Run lint, typecheck, tests, and build where applicable.
- [ ] For migrations: dry-run diff → approval → apply.
- [ ] Preserve relative paths and verify the actual runtime import path.
- [ ] Run compile/health checks on the deployed path.
- [ ] Check cron/worker locks, retry, reaper, and terminal queue state.
- [ ] Reconcile Admin UI ↔ API ↔ DB ↔ ERP after deployment.
- [ ] Update implementation notes, channel map, handoff, and lightweight personal index.
- [ ] Record deviations and quiz the operator on 2–3 core decisions.
