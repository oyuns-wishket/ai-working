#!/usr/bin/env node

import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import { execFileSync, spawn } from "node:child_process"

const RECENT_SESSION_MS = 45 * 60 * 1000
const DOCKER_BUSY_MS = 5 * 60 * 1000
const DOCKER_PENDING_TTL_MS = 10 * 60 * 1000
const SAFE_NAME = /^[a-zA-Z0-9_.-]+$/
const CONTAINER_ID = /^[a-f0-9]{64}$/

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
      "RESOURCE_PRESSURE: 새 dev/build/Supabase 작업 전에 사용하지 않는 local stack을 `supabase stop --project-id <id>`로 정리한다. volume은 삭제하지 않는다.",
    )
  } else {
    lines.push(
      "RESOURCE_OK: local Supabase는 동시에 한 stack만 실행하고, 소유권이 확인된 컨테이너와 유휴 Docker Desktop은 SessionEnd에서 자동 정리된다. 그 외 자원은 세션에서 직접 정리한다.",
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

function buildCleanupScript({ containers, supabase, quitApp }) {
  const steps = []
  if (containers.length) {
    steps.push(`docker stop -t 3 ${containers.join(" ")} >/dev/null 2>&1`)
  }
  if (supabase) {
    steps.push(
      `cd ${shellQuote(supabase.root)} && supabase stop --project-id ${supabase.projectId} >/dev/null 2>&1`,
    )
  }
  if (quitApp) {
    // 남은 컨테이너가 정말 하나도 없을 때만 Docker Desktop(VM 포함)을 내린다.
    steps.push(
      `sleep 2; remaining=$(docker ps -q 2>/dev/null) && if [ -z "$remaining" ]; then docker desktop stop --detach --force >/dev/null 2>&1 || osascript -e 'quit app "Docker"' >/dev/null 2>&1; fi`,
    )
  }
  return steps.join("; ")
}

function cleanupSession(input) {
  const file = sessionFile(input)
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
  removeFile(file)

  const claimedElsewhere = new Set(
    otherRecentSessions(file).flatMap(({ value }) => value.dockerOwned || []),
  )
  const toStop = owned.filter((id) => !claimedElsewhere.has(id) && inspectContainer(id)?.running)

  let supabase = null
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
        supabase = { root: session.root, projectId: session.projectId }
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

  if (!toStop.length && !supabase && !quitApp) return
  detach(buildCleanupScript({ containers: toStop, supabase, quitApp }))
}

async function main() {
  const input = await readStdin()
  const event = String(input.hook_event_name || "")
  if (!["UserPromptSubmit", "PreToolUse", "PostToolUse", "SessionEnd"].includes(event)) return

  // Missing session identity must never share an ownership marker with another turn.
  if (!input.session_id && event !== "UserPromptSubmit") return

  if (event === "SessionEnd") {
    cleanupSession(input)
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
          additionalContext: formatContext(snapshot, session),
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

main().catch(() => process.exit(0))
