import assert from "node:assert/strict"
import test from "node:test"
import { cleanupArchivedAgent } from "../plugins/paseo-resource-cleanup/server/cleanup.mjs"

const event = {
  agent: { id: "agent-one", provider: "codex", cwd: "/work/example" },
  archivedAt: "2026-01-01T00:00:00.000Z",
}
const snapshot = {
  ...event.agent, archivedAt: event.archivedAt, status: "closed", activeTurn: null,
  persistence: { provider: "codex", sessionId: "native-one" },
}

function fixture(states, statuses = ["dispatched"]) {
  let time = 0
  const calls = []
  let refreshes = 0
  const controller = new AbortController()
  const context = { signal: controller.signal, paseo: { agents: { ref(id) {
    assert.equal(id, event.agent.id)
    return { async refresh() {
      const state = states[Math.min(refreshes++, states.length - 1)]
      return state ? { agent: state } : null
    } }
  } } } }
  const options = {
    now: () => time, timeoutMs: 500,
    wait: async ms => { time += ms },
    run: async input => { calls.push(input); return statuses[Math.min(calls.length - 1, statuses.length - 1)] },
  }
  return { calls, context, options, controller, refreshes: () => refreshes }
}

test("archive waits for runtime closure before invoking the native session guard", async () => {
  const f = fixture([{ ...snapshot, status: "running", activeTurn: { turnId: "turn" } }, snapshot])
  assert.equal(await cleanupArchivedAgent(event, f.context, f.options), "dispatched")
  assert.equal(f.refreshes(), 2)
  assert.deepEqual(f.calls, [{ hook_event_name: "SessionEnd", session_id: "native-one", cwd: "/work/example", reason: "other" }])
})

test("supports Claude native identity too", async () => {
  const f = fixture([{ ...snapshot, provider: "claude", persistence: { provider: "claude", sessionId: "claude-one" } }])
  await cleanupArchivedAgent({ ...event, agent: { ...event.agent, provider: "claude" } }, f.context, f.options)
  assert.equal(f.calls[0].session_id, "claude-one")
})

test("missing, restored, mismatched and unsafe snapshots never cause cleanup", async t => {
  for (const state of [null, { ...snapshot, archivedAt: null }, { ...snapshot, archivedAt: "new-archive" },
    { ...snapshot, id: "another" }, { ...snapshot, provider: "claude" }, { ...snapshot, cwd: "/other" },
    { ...snapshot, persistence: null }, { ...snapshot, persistence: { provider: "claude", sessionId: "native-one" } },
    { ...snapshot, persistence: { provider: "codex", sessionId: "../escape" } }]) {
    await t.test(JSON.stringify(state), async () => {
      const f = fixture([state])
      await cleanupArchivedAgent(event, f.context, f.options)
      assert.equal(f.calls.length, 0)
    })
  }
})

test("a replaced native session is not cleaned up by an old archive event", async () => {
  const f = fixture([{ ...snapshot, status: "running" }, { ...snapshot, persistence: { provider: "codex", sessionId: "new-session" } }])
  assert.equal(await cleanupArchivedAgent(event, f.context, f.options), "changed-session")
  assert.equal(f.calls.length, 0)
})

test("busy native cleanup is retried with a fresh archive/identity check", async () => {
  const f = fixture([snapshot], ["busy", "absent"])
  assert.equal(await cleanupArchivedAgent(event, f.context, f.options), "absent")
  assert.equal(f.refreshes(), 2)
})

test("closure timeout, abort and guard failures surface instead of claiming success", async () => {
  const f = fixture([{ ...snapshot, status: "idle" }])
  await assert.rejects(cleanupArchivedAgent(event, f.context, f.options), /timed out/)
  assert.equal(f.calls.length, 0)
  f.controller.abort()
  await assert.rejects(cleanupArchivedAgent(event, f.context, f.options), /abort/i)
  const g = fixture([snapshot])
  g.options.run = async () => { throw new Error("guard failure") }
  await assert.rejects(cleanupArchivedAgent(event, g.context, g.options), /guard failure/)
})
