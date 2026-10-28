#!/usr/bin/env node

import fs from "node:fs"
import { createHash } from "node:crypto"
import os from "node:os"
import path from "node:path"
import { execFileSync, spawn } from "node:child_process"
import { fileURLToPath } from "node:url"

const RECENT_SESSION_MS = 45 * 60 * 1000
const DOCKER_BUSY_MS = 5 * 60 * 1000
const DOCKER_PENDING_TTL_MS = 10 * 60 * 1000
const SAFE_NAME = /^[a-zA-Z0-9_.-]+$/
const CONTAINER_ID = /^[a-f0-9]{64}$/
const DEV_SERVER_MIN_BYTES = 4 * 1024 ** 3
// Dev servers keep compiled routes in memory; vitest and build commands do not match.
const DEV_SERVER = /(^|[\s/])(next-server\b|next dev\b|vite(\s|$)|nuxi? dev\b|astro dev\b|remix dev\b|webpack(-dev-server\b| serve\b))/

function readStdin() {
  return new Promise((resolve) => {
    let raw = ""
    process.stdin.setEncoding("utf8")
    process.stdin.on("data", (chunk) => (raw += chunk))
    process.stdin.on("end", () => {
      try {
        resolve(JSON.parse(raw || "{}"))
      } catch {
        resolve({})
      }
    })
  })
}

function run(command, args, options = {}) {
  try {
    return execFileSync(command, args, {
      cwd: options.cwd,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      timeout: options.timeout ?? 900,
      env: process.env,
    }).trim()
  } catch {
    return ""
  }
}

// SessionEnd 정리는 세션 종료를 붙잡지 않도록 분리된 프로세스에 넘긴다.
function detach(script) {
  try {
    const child = spawn("/bin/sh", ["-c", script], {
      detached: true,
      stdio: "ignore",
      env: process.env,
    })
    child.unref()
    return true
  } catch {
    return false
  }
}

function cacheRoot() {
  return (
    process.env.AGENT_RESOURCE_GUARD_CACHE_DIR ||
    path.join(os.homedir(), ".cache", "ai-working-resource-guard")
  )
}

function safeSessionId(input) {
  return String(input.session_id || "unknown").replace(/[^a-zA-Z0-9_.-]/g, "_")
}

function sessionFile(input) {
  return path.join(cacheRoot(), "sessions", `${safeSessionId(input)}.json`)
}

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"))
  } catch {
    return null
  }
}

function writeJson(file, value) {
  try {
    fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 })
    fs.writeFileSync(file, `${JSON.stringify(value)}\n`, { mode: 0o600 })
  } catch {
    // Cache failure must not break the agent turn.
  }
}

function removeFile(file) {
  try {
    fs.unlinkSync(file)
  } catch {
    // Missing ownership marker is already clean.
  }
}

function findSupabaseProject(start) {
  let current = path.resolve(start)
  while (true) {
    const config = path.join(current, "supabase", "config.toml")
    try {
      const content = fs.readFileSync(config, "utf8")
      const match = content.match(/^project_id\s*=\s*["']([a-zA-Z0-9._-]+)["']/m)
      if (match) return { root: current, projectId: match[1] }
    } catch {
      // Keep walking to the filesystem root.
    }
    const parent = path.dirname(current)
    if (parent === current) return null
    current = parent
  }
}

function dockerEngineUp() {
  if (process.env.AGENT_RESOURCE_GUARD_FORCE_DOCKER === "1") return true
  return Boolean(
    run("pgrep", ["-f", "com\\.apple\\.Virtualization\\.VirtualMachine"], { timeout: 250 }),
  )
}

function runningContainers() {
  if (!dockerEngineUp()) return []
  const names = run("docker", ["ps", "--format", "{{.Names}}"], { timeout: 1200 })
  if (!names) return []
  return names
    .split("\n")
    .map((name) => name.trim())
    .filter(Boolean)
}

function supabaseStacksOf(containers) {
  return [
    ...new Set(containers.map((name) => name.match(/^supabase_db_(.+)$/)?.[1]).filter(Boolean)),
  ].sort()
}

function memorySnapshot() {
  const pressure = run("memory_pressure", ["-Q"], { timeout: 700 })
  const swap = run("sysctl", ["vm.swapusage"], { timeout: 700 })
  const freeMatch = pressure.match(/memory free percentage:\s*(\d+)%/i)
  const swapMatch = swap.match(/used\s*=\s*([\d.]+)([MG])/i)
  let swapUsedMb = null
  if (swapMatch) {
    swapUsedMb = Number(swapMatch[1]) * (swapMatch[2].toUpperCase() === "G" ? 1024 : 1)
  }
  return {
    freePercent: freeMatch ? Number(freeMatch[1]) : null,
    swapUsedMb: Number.isFinite(swapUsedMb) ? swapUsedMb : null,
  }
}

// Measured only in the pressure branch. RSS omits compressed and swapped pages, so use
// footprint (macOS); where it is missing the list stays empty.
function largeDevServers() {
  const pids = run("ps", ["-axo", "pid=,command="], { timeout: 700 })
    .split("\n")
    .map((line) => line.trim().match(/^(\d+)\s+(.*)$/))
    .filter((match) => match && DEV_SERVER.test(match[2]))
    .map((match) => match[1])
    .slice(0, 20)
  if (!pids.length) return []
  const measured = run("footprint", ["-f", "bytes", "--noCategories", ...pids.flatMap((pid) => ["--pid", pid])], { timeout: 1200 })
  return [...measured.matchAll(/\[(\d+)\]:.*?Footprint:\s*(\d+) B/g)]
    .map((match) => ({ pid: match[1], bytes: Number(match[2]) }))
    .filter((server) => pids.includes(server.pid) && server.bytes >= DEV_SERVER_MIN_BYTES)
    .sort((a, b) => b.bytes - a.bytes)
    .slice(0, 3)
    .map((server) => {
      const cwd = run("lsof", ["-a", "-p", server.pid, "-d", "cwd", "-Fn"], { timeout: 300 })
        .split("\n").find((line) => line.startsWith("n"))?.slice(1)
      return { ...server, cwd: cwd || "unknown" }
    })
}

function resourceSnapshot() {
  const containers = runningContainers()
  return { ...memorySnapshot(), containers, stacks: supabaseStacksOf(containers) }
}

function isCritical(snapshot) {
  return (
    (snapshot.freePercent !== null && snapshot.freePercent < 15) ||
    (snapshot.swapUsedMb !== null && snapshot.swapUsedMb >= 8 * 1024)
  )
}

function formatContext(snapshot, session) {
  const free = snapshot.freePercent === null ? "unknown" : `${snapshot.freePercent}%`
  const swap =
    snapshot.swapUsedMb === null ? "unknown" : `${(snapshot.swapUsedMb / 1024).toFixed(1)}GB`
  const stacks = snapshot.stacks.length ? snapshot.stacks.join(",") : "none"
  const owned = (session?.dockerOwned || []).length
  const lines = [
    "[Dev Resource Guard]",
    `memory_free=${free} swap_used=${swap} supabase_stacks=${stacks} docker_containers=${snapshot.containers.length} session_owned=${owned}`,
  ]
  if (isCritical(snapshot) || snapshot.stacks.length > 1) {
    lines.push(
      "RESOURCE_PRESSURE: 새 dev/build/Supabase 작업 전에 이번 작업이 띄운 dev server와 사용하지 않는 local stack(`supabase stop --project-id <id>`)을 정리한다. volume은 삭제하지 않는다. 다른 세션의 자원은 끄지 말고 PID·용량·경로를 사용자에게 보고한다.",
    )
    const servers = largeDevServers()
    if (servers.length) {
      const listed = servers.map(({ pid, bytes, cwd }) => `pid=${pid} ${(bytes / 1024 ** 3).toFixed(1)}GB cwd=${cwd}`)
      lines.push(`LARGE_DEV_SERVERS: ${listed.join("; ")} — 여러 화면 순회는 production build 서버에서 돌린다(dev-protocol local-operations).`)
    }
  } else {
    lines.push(
      "RESOURCE_OK: local Supabase는 동시에 한 stack만 실행하고, 추적된 컨테이너는 종료하고 ai-working.disposable=true 컨테이너만 삭제한다(volume 보존). managed-server.py로 시작한 임시 서버도 종료한다. 미등록 자원은 직접 정리하며 결과는 ~/.cache/ai-working-resource-guard/*-results/에서 확인한다.",
    )
  }
  return lines.join("\n")
}

function deny(reason) {
  process.stdout.write(
    `${JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: `Dev Resource Guard: ${reason}`,
      },
    })}\n`,
  )
}

function updateSession(input, patch) {
  const file = sessionFile(input)
  const previous = readJson(file) || {}
  const next = {
    ...previous,
    ...patch,
    sessionId: safeSessionId(input),
    lastSeenAt: Date.now(),
  }
  writeJson(file, next)
  return next
}

function recordSupabase(input, project, owns) {
  const previous = readJson(sessionFile(input))
  return updateSession(input, {
    root: project.root,
    projectId: project.projectId,
    owns: Boolean(owns || previous?.owns),
  })
}

// 컨테이너를 새로 띄우는 명령인지 판정한다. down/stop/ps 같은 조회·정리 명령은 제외된다.
function isDockerStartCommand(command) {
  return (
    /\bdocker\s+compose\b[^\n;&|]*\bup\b/i.test(command) ||
    /\bdocker-compose\b[^\n;&|]*\bup\b/i.test(command) ||
    /\bdocker\s+(run|start|create)\b/i.test(command)
  )
}

function touchesDocker(command) {
  return /\b(docker|docker-compose|supabase)\b/i.test(command)
}

// A successful tool result and immutable IDs establish ownership. A before/after
// name difference alone cannot distinguish another session's concurrent work.
function inspectContainer(target) {
  if (!SAFE_NAME.test(target)) return null
  const output = run("docker", ["inspect", "--format", '{{.Id}} {{.Name}} {{.State.Running}} {{index .Config.Labels "com.supabase.cli.project"}}', target])
  const match = output.match(/^([a-f0-9]{64}) \/?([a-zA-Z0-9_.-]+) (true|false)(?: (.*))?$/)
  return match ? { id: match[1], name: match[2], running: match[3] === "true", supabaseProject: match[4] || null } : null
}

function simpleCommand(command) {
  // Compound commands, substitutions, redirects and wrappers need explicit
  // manual cleanup. Do not guess which command produced the observed output.
  return !/[\n;&|`$<>]/.test(command) && !/["'\\]/.test(command)
}

function successfulResult(input) {
  const response = input.tool_response
  if (!response || typeof response !== "object" || response.interrupted || response.isError || response.error) return false
  const exitCode = response.exit_code ?? response.exitCode
  return exitCode === undefined || exitCode === 0
}

function scopedContainers(names, projectId) {
  return names.filter((name) => name.startsWith("supabase_") && name.endsWith(`_${projectId}`))
    .map(inspectContainer).filter((container) => container?.running && container.supabaseProject === projectId)
}

function confirmOwnership(input, command) {
  const session = readJson(sessionFile(input))
  const pending = session?.dockerPending
  if (!pending || pending.command !== command ||
      (pending.toolUseId && pending.toolUseId !== input.tool_use_id)) return
  updateSession(input, { dockerPending: null })
  if (Date.now() - Number(pending.at || 0) > DOCKER_PENDING_TTL_MS) return
  // Native Codex exposes raw tool text without an exit code. A sole immutable
  // ID from run/create, resolved by inspect below, is attributable evidence;
  // arbitrary text cannot prove that docker start or Supabase succeeded.
  const nativeContainerId = pending.kind === "run" && typeof input.tool_response === "string"
    && CONTAINER_ID.test(input.tool_response.trim())
  if (!successfulResult(input) && !nativeContainerId) return

  if (pending.kind === "supabase") {
    const containers = scopedContainers(runningContainers(), pending.projectId)
    if (!containers.some((container) => container.name === `supabase_db_${pending.projectId}`)) return
    updateSession(input, {
      root: pending.root, projectId: pending.projectId, owns: true,
      ownershipVersion: 2, supabaseContainerIds: containers.map((container) => container.id),
    })
    return
  }

  let confirmed = []
  if (pending.kind === "run") {
    const output = typeof input.tool_response === "string" ? input.tool_response.trim()
      : String(input.tool_response.stdout ?? input.tool_response.output ?? "").trim()
    if (!CONTAINER_ID.test(output)) return
    const container = inspectContainer(output)
    if (container && !pending.before.includes(container.name)) confirmed = [container.id]
  } else if (pending.kind === "start") {
    confirmed = (pending.targets || []).filter((id) => inspectContainer(id)?.running)
  }
  updateSession(input, {
    ownershipVersion: 2,
    dockerOwned: [...new Set([...(session.ownershipVersion === 2 ? session.dockerOwned || [] : []), ...confirmed])],
  })
}

function otherRecentSessions(excludedFile) {
  const directory = path.join(cacheRoot(), "sessions")
  let files = []
  try {
    files = fs.readdirSync(directory).map((name) => path.join(directory, name))
  } catch {
    return []
  }
  return files
    .filter((file) => file !== excludedFile)
    .map((file) => ({ file, value: readJson(file) }))
    .filter(({ value }) => value && Date.now() - Number(value.lastSeenAt || 0) < RECENT_SESSION_MS)
    .sort((a, b) => Number(b.value.lastSeenAt) - Number(a.value.lastSeenAt))
}

function supabaseObservers(projectId, excludedFile) {
  return otherRecentSessions(excludedFile).filter(({ value }) => value.projectId === projectId)
}

// 다른 세션이 방금까지 docker를 만지고 있었다면 Docker Desktop을 끄지 않는다.
function dockerBusyElsewhere(excludedFile) {
  return otherRecentSessions(excludedFile).some(
    ({ value }) =>
      (value.dockerOwned || []).length > 0 ||
      Date.now() - Number(value.dockerTouchedAt || 0) < DOCKER_BUSY_MS,
  )
}

function shellQuote(value) {
  return `'${String(value).replace(/'/g, "'\\''")}'`
}

function dispatchCleanup(plan) {
  const directory = path.dirname(fileURLToPath(import.meta.url))
  const child = spawn("python3", [
    path.join(directory, "resource-cleanup-lock.py"),
    path.join(cacheRoot(), "worker-locks", `${plan.sessionId}.lock`),
    process.execPath, path.join(directory, "resource-cleanup-worker.mjs"),
  ], { detached: true, stdio: ["pipe", "ignore", "ignore"] })
  child.on("error", () => {}) // Ownership remains available for retry.
  child.stdin.on("error", () => {})
  child.stdin.end(JSON.stringify(plan))
  child.unref()
}

function cleanupProcesses(input) {
  const sessionId = safeSessionId(input)
  const directory = path.join(cacheRoot(), "processes", sessionId)
  if (!fs.existsSync(directory) || !fs.readdirSync(directory).some(n => n.endsWith(".json"))) return
  const helper = path.join(path.dirname(fileURLToPath(import.meta.url)), "managed-server.py")
  return detach(`python3 ${shellQuote(helper)} --session ${shellQuote(sessionId)} cleanup`)
}

function cleanupSession(input) {
  const processCleanup = cleanupProcesses(input)
  const file = sessionFile(input)
  if (!fs.existsSync(file)) return processCleanup ? "dispatched" : "absent"
  // flock releases on process death, unlike stale PID files. The helper execs
  // this same program with the lock inherited for the duration of cleanup.
  if (process.argv.includes("--cleanup-locked")) {
    cleanupOwnedSession(input, file)
    return "dispatched"
  }
  const script = fileURLToPath(import.meta.url)
  const output = execFileSync("python3", [
    path.join(path.dirname(script), "resource-cleanup-lock.py"),
    path.join(cacheRoot(), "cleanup-locks", `${safeSessionId(input)}.lock`),
    process.execPath, script,
  ], { input: JSON.stringify(input), encoding: "utf8", timeout: 15000 })
  return JSON.parse(output).status
}

function cleanupOwnedSession(input, file) {
  const session = readJson(file)
  if (session?.ownershipVersion !== 2) {
    removeFile(file)
    return
  }
  const containers = runningContainers()

  // Legacy name-based markers and unconfirmed pending commands cannot authorize
  // cleanup. In particular, never claim containers just because they appeared.
  const owned = session?.ownershipVersion === 2
    ? (session.dockerOwned || []).filter((id) => CONTAINER_ID.test(id)) : []
  const claimedElsewhere = new Set(
    otherRecentSessions(file).flatMap(({ value }) => value.dockerOwned || []),
  )
  const exclusive = owned.filter((id) => !claimedElsewhere.has(id))
  const toStop = exclusive.filter((id) => inspectContainer(id)?.running)
  const disposable = exclusive // Worker reads the opt-in label; failed probes retain evidence.

  let supabase = null
  let unresolvedSupabase = false
  if (session?.ownershipVersion === 2 && session.owns && SAFE_NAME.test(session.projectId || "")) {
    const observers = supabaseObservers(session.projectId, file)
    if (observers.length) {
      const nextOwner = observers[0]
      writeJson(nextOwner.file, {
        ...nextOwner.value, owns: true, ownershipVersion: 2,
        supabaseContainerIds: session.supabaseContainerIds,
      })
    } else {
      const current = scopedContainers(containers, session.projectId).map((container) => container.id).sort()
      const expected = [...(session.supabaseContainerIds || [])].filter((id) => CONTAINER_ID.test(id)).sort()
      if (expected.length && JSON.stringify(current) === JSON.stringify(expected)) {
        supabase = { root: session.root, projectId: session.projectId, ids: expected }
      } else {
        unresolvedSupabase = true
      }
    }
  }

  const supabaseContainerCount = supabase
    ? session.supabaseContainerIds.length
    : 0
  const remaining = containers.length - toStop.length - supabaseContainerCount
  const keepApp = process.env.AGENT_DOCKER_GUARD_KEEP === "1"
  const quitApp =
    !keepApp && (toStop.length > 0 || supabase !== null) && dockerEngineUp() && remaining <= 0 && !dockerBusyElsewhere(file)

  if (!exclusive.length && !supabase && !quitApp && !unresolvedSupabase) {
    removeFile(file)
    return
  }
  dispatchCleanup({
    containers: exclusive, disposable, supabase, quitApp, unresolvedSupabase,
    cache: cacheRoot(), file, sessionId: safeSessionId(input),
    fingerprint: createHash("sha256").update(fs.readFileSync(file)).digest("hex"),
  })

}

async function main() {
  const input = await readStdin()
  const event = String(input.hook_event_name || "")
  if (!["UserPromptSubmit", "PreToolUse", "PostToolUse", "SessionEnd"].includes(event)) return

  // Missing session identity must never share an ownership marker with another turn.
  if (!input.session_id && event !== "UserPromptSubmit") return

  if (event === "SessionEnd") {
    const status = cleanupSession(input)
    if (process.argv.includes("--archive-cleanup")) {
      process.stdout.write(`${JSON.stringify({ status })}\n`)
    }
    return
  }

  const tool = String(input.tool_name || "")
  const command = String(input.tool_input?.command || input.tool_input?.cmd || "")
  // Unrelated tool calls must not execute Docker or OS memory probes.
  if (event !== "UserPromptSubmit" && (tool !== "Bash" || !touchesDocker(command))) return
  if (event === "PostToolUse") {
    confirmOwnership(input, command)
    return
  }

  const cwd = path.resolve(input.cwd || process.cwd())
  const project = findSupabaseProject(cwd)
  const snapshot = resourceSnapshot()
  let session = readJson(sessionFile(input))

  if (event === "UserPromptSubmit") {
    if (input.session_id && project && snapshot.stacks.includes(project.projectId)) {
      session = recordSupabase(input, project, false)
    }
    process.stdout.write(
      `${JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "UserPromptSubmit",
          additionalContext: formatContext(snapshot, session) + (input.session_id
            ? `\nTEMP_SERVER: python3 ~/.claude/hooks/managed-server.py --session ${safeSessionId(input)} start -- <server-command> (현재 세션 임시 서버는 이 launcher로 실행)` : ""),
        },
      })}\n`,
    )
    return
  }

  updateSession(input, { dockerTouchedAt: Date.now() })

  if (isDockerStartCommand(command)) {
    let pending = null
    if (simpleCommand(command) && /^\s*docker\s+(run|create)\s+/.test(command)) {
      pending = { kind: "run", before: snapshot.containers }
    } else if (simpleCommand(command) && /^\s*docker\s+start\s+([a-zA-Z0-9_.-]+\s*)+$/.test(command)) {
      const targets = command.trim().split(/\s+/).slice(2).map(inspectContainer)
        .filter((container) => container && !container.running).map((container) => container.id)
      pending = { kind: "start", targets }
    }
    updateSession(input, { dockerPending: pending ? {
      ...pending, at: Date.now(), command, toolUseId: input.tool_use_id,
    } : null })
    return
  }

  if (!/\bsupabase\s+start\b/i.test(command)) return
  if (!project) {
    deny("Supabase project root 밖에서는 local stack을 시작할 수 없다.")
    return
  }

  const otherStacks = snapshot.stacks.filter((id) => id !== project.projectId)
  if (otherStacks.length) {
    deny(`다른 local stack이 실행 중이다: ${otherStacks.join(", ")}. 먼저 해당 stack을 stop한다.`)
    return
  }
  if (isCritical(snapshot)) {
    deny("메모리/swap이 임계 상태다. 불필요한 개발 자원을 정리한 뒤 다시 시작한다.")
    return
  }

  // Only the plain, cwd-scoped start has an unambiguous target. Flags such as
  // --workdir can select another project and are intentionally not auto-owned.
  if (!snapshot.stacks.includes(project.projectId) && /^\s*supabase\s+start\s*$/.test(command)) {
    updateSession(input, { dockerPending: {
      kind: "supabase", at: Date.now(), command, toolUseId: input.tool_use_id,
      root: project.root, projectId: project.projectId,
    } })
  }
}

main().catch(() => process.exit(process.argv.includes("--archive-cleanup") ? 1 : 0))
