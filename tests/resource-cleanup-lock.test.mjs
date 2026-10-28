import assert from "node:assert/strict"
import test from "node:test"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import { spawn, execFileSync } from "node:child_process"
import { once } from "node:events"

const guard = path.resolve("hooks/dev-resource-guard.mjs")
const helper = path.resolve("hooks/resource-cleanup-lock.py")

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "resource-lock-test-"))
  t.after(() => fs.rmSync(root, { recursive: true, force: true }))
  fs.mkdirSync(path.join(root, "sessions"))
  return root
}

function invoke(root) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [guard, "--archive-cleanup"], {
      env: { ...process.env, AGENT_RESOURCE_GUARD_CACHE_DIR: root },
      stdio: ["pipe", "pipe", "pipe"],
    })
    let output = ""
    child.stdout.on("data", chunk => { output += chunk })
    child.stderr.resume()
    child.on("error", reject)
    child.on("close", code => {
      try { assert.equal(code, 0); resolve(JSON.parse(output).status) } catch (error) { reject(error) }
    })
    child.stdin.end(JSON.stringify({ hook_event_name: "SessionEnd", session_id: "probe" }))
  })
}

test("concurrent native and archive cleanup consume the marker once", async t => {
  const root = fixture(t)
  const marker = path.join(root, "sessions/probe.json")
  fs.writeFileSync(marker, JSON.stringify({ ownershipVersion: 0 }))
  const results = await Promise.all(Array.from({ length: 8 }, () => invoke(root)))
  assert.equal(results.filter(status => status === "dispatched").length, 1)
  assert(results.every(status => ["dispatched", "busy", "absent"].includes(status)))
  assert.equal(fs.existsSync(marker), false)
})

test("OS lock survives exec, rejects a live duplicate, and releases after SIGKILL", async t => {
  const root = fixture(t)
  const worker = path.join(root, "worker.mjs")
  const lock = path.join(root, "cleanup-locks/probe.lock")
  fs.writeFileSync(worker, 'console.log("ready"); setInterval(() => {}, 1000)')
  const holder = spawn("python3", [helper, lock, process.execPath, worker], { stdio: ["ignore", "pipe", "pipe"] })
  t.after(() => { if (holder.exitCode === null && holder.signalCode === null) holder.kill("SIGKILL") })
  await once(holder.stdout, "data")
  const busy = execFileSync("python3", [helper, lock, process.execPath, worker], { encoding: "utf8" })
  assert.equal(JSON.parse(busy).status, "busy")
  const exit = once(holder, "exit")
  holder.kill("SIGKILL")
  await exit
  fs.writeFileSync(worker, 'console.log(JSON.stringify({status:"acquired"}))')
  const next = execFileSync("python3", [helper, lock, process.execPath, worker], { encoding: "utf8" })
  assert.equal(JSON.parse(next).status, "acquired")
  assert.equal(fs.existsSync(lock), true, "never unlink lock files while another caller may hold their inode")
})
