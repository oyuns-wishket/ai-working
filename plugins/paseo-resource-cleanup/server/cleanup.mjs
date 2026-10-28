import os from "node:os"
import path from "node:path"
import { spawn } from "node:child_process"
import { setTimeout as delay } from "node:timers/promises"

const SESSION_ID = /^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,199}$/

// Invoke only our installed resource guard, never arbitrary SessionEnd hooks.
// The guard owns container identity, cross-session sharing, and detached cleanup.
export function runGuard(input, signal) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [
      path.join(os.homedir(), ".claude", "hooks", "dev-resource-guard.mjs"),
      "--archive-cleanup",
    ], { stdio: ["pipe", "pipe", "pipe"], signal, timeout: 10000 })
    let output = ""
    child.stdout.on("data", chunk => { output = (output + chunk).slice(-4096) })
    // Drain errors without leaking environment or command payloads into logs.
    child.stderr.resume()
    child.on("error", reject)
    child.stdin.on("error", reject)
    child.on("close", code => {
      if (code !== 0) return reject(new Error(`Resource guard exited with code ${code}`))
      try {
        const result = JSON.parse(output)
        if (!["absent", "busy", "dispatched"].includes(result.status)) throw new Error()
        resolve(result.status)
      } catch { reject(new Error("Resource guard returned no valid cleanup status")) }
    })
    child.stdin.end(JSON.stringify(input))
  })
}

export async function cleanupArchivedAgent(event, context, options = {}) {
  const { run = runGuard, wait = delay, now = Date.now, timeoutMs = 20000 } = options
  if (!["claude", "codex"].includes(event.agent.provider)) return "unsupported-provider"
  const handle = context.paseo.agents.ref(event.agent.id)
  const deadline = now() + timeoutMs
  let sessionId = null
  while (now() < deadline) {
    context.signal.throwIfAborted()
    const response = await handle.refresh()
    const agent = response?.agent
    // Missing, restored, re-archived, or replaced agents must never authorize
    // cleanup of a newer session through an old event.
    if (!agent || agent.id !== event.agent.id || agent.provider !== event.agent.provider ||
        agent.cwd !== event.agent.cwd || agent.archivedAt !== event.archivedAt) return "changed-agent"
    const currentId = agent.persistence?.sessionId
    if (!SESSION_ID.test(currentId ?? "") || agent.persistence?.provider !== agent.provider) return "missing-session"
    if (sessionId && currentId !== sessionId) return "changed-session"
    sessionId = currentId
    if (agent.status === "closed" && !agent.activeTurn) {
      const status = await run({
        hook_event_name: "SessionEnd", session_id: sessionId, cwd: agent.cwd, reason: "other",
      }, context.signal)
      if (status !== "busy") return status
    }
    await wait(100, undefined, { signal: context.signal })
  }
  throw new Error("Archive cleanup timed out waiting for a closed session or resource guard lock")
}

export default function contribute(server) {
  const pending = new Map()
  return server.on("agent.archived", async (event, context) => {
    // Workspace archive emits this event for each owned agent too.
    const key = `${event.agent.id}:${event.archivedAt}`
    if (pending.has(key)) return pending.get(key)
    const task = cleanupArchivedAgent(event, context).then(status => {
      console.info(JSON.stringify({ event: "archive-resource-cleanup", agentId: event.agent.id, status }))
    })
    pending.set(key, task)
    try { await task } finally { pending.delete(key) }
  })
}
