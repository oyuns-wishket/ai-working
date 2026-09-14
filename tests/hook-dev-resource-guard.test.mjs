import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import { createHash } from "node:crypto"
import { execFileSync } from "node:child_process"

const script = path.resolve("hooks/dev-resource-guard.mjs")
const temp = fs.mkdtempSync(path.join(os.tmpdir(), "dev-resource-guard-test-"))
const repo = path.join(temp, "example-erp")
const bin = path.join(temp, "bin")
const cache = path.join(temp, "cache")
const stopLog = path.join(temp, "supabase-stop.log")
const dockerLog = path.join(temp, "docker.log")
const probeLog = path.join(temp, "probe.log")
const cid = (name) => createHash("sha256").update(name).digest("hex")

function fake(name, content) {
  const file = path.join(bin, name)
  fs.writeFileSync(file, `#!/bin/sh\n${content}\n`)
  fs.chmodSync(file, 0o755)
}

function invoke(payload, extraEnv = {}) {
  const output = execFileSync(process.execPath, [script], {
    cwd: repo,
    input: JSON.stringify(payload),
    encoding: "utf8",
    env: {
      ...process.env,
      PATH: `${bin}:${process.env.PATH}`,
      AGENT_RESOURCE_GUARD_CACHE_DIR: cache,
      AGENT_RESOURCE_GUARD_FORCE_DOCKER: "1",
      // 정리는 detach된 자식이 수행하므로 앱 종료는 해당 시나리오에서만 연다.
      AGENT_DOCKER_GUARD_KEEP: "1",
      TEST_FREE_PERCENT: "40",
      TEST_SWAP_MB: "1024",
      TEST_STACKS: "",
      TEST_STACKS_AFTER: "",
      TEST_STOP_LOG: stopLog,
      TEST_DOCKER_LOG: dockerLog,
      TEST_PROBE_LOG: probeLog,
      ...extraEnv,
    },
  }).trim()
  return output ? JSON.parse(output) : null
}

// SessionEnd 정리는 detach된 프로세스가 수행한다. 완료를 기다리되 무한정 걸리지 않게 한다.
function waitFor(predicate, label, timeoutMs = 5000) {
  const idle = new Int32Array(new SharedArrayBuffer(4))
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    if (predicate()) return
    Atomics.wait(idle, 0, 0, 25)
  }
  assert.fail(`timed out waiting for ${label}`)
}

function settle(ms = 400) {
  const idle = new Int32Array(new SharedArrayBuffer(4))
  Atomics.wait(idle, 0, 0, ms)
}

function readLog(file) {
  return fs.existsSync(file) ? fs.readFileSync(file, "utf8") : ""
}

try {
  fs.mkdirSync(path.join(repo, "supabase"), { recursive: true })
  fs.mkdirSync(bin, { recursive: true })
  fs.writeFileSync(path.join(repo, "supabase", "config.toml"), 'project_id = "example-erp"\n')

  fake("memory_pressure", 'printf "memory_pressure\\n" >> "$TEST_PROBE_LOG"; printf "System-wide memory free percentage: %s%%\\n" "$TEST_FREE_PERCENT"')
  fake("sysctl", 'printf "sysctl\\n" >> "$TEST_PROBE_LOG"; printf "vm.swapusage: total = 10240.00M used = %sM free = 0.00M\\n" "$TEST_SWAP_MB"')
  const dockerMock = `#!${process.execPath}
const fs = require("node:fs")
const { createHash } = require("node:crypto")
const args = process.argv.slice(2)
if (["ps", "inspect"].includes(args[0])) fs.appendFileSync(process.env.TEST_PROBE_LOG, args.join(" ") + "\\n")
if (args[0] === "ps") {
  process.stdout.write((args[1] === "-q" ? process.env.TEST_STACKS_AFTER : process.env.TEST_STACKS) || "")
} else if (args[0] === "inspect") {
  const names = (process.env.TEST_STACKS || "").split("\\n").filter(Boolean)
  const entries = names.map(name => ({name, id: createHash("sha256").update(name).digest("hex"), running: true}))
  entries.push(...JSON.parse(process.env.TEST_INSPECT || "[]"))
  const match = entries.find(entry => entry.name === args.at(-1) || entry.id === args.at(-1))
  if (!match) process.exit(1)
  const project = match.projectId ?? (match.name.startsWith("supabase_db_") ? match.name.slice(12) : "<no value>")
  process.stdout.write(match.id + " /" + match.name + " " + match.running + " " + project)
} else {
  fs.appendFileSync(process.env.TEST_DOCKER_LOG, "docker " + args.join(" ") + "\\n")
}
`
  fs.writeFileSync(path.join(bin, "docker"), dockerMock)
  fs.chmodSync(path.join(bin, "docker"), 0o755)
  fake("supabase", 'printf "%s\\n" "$*" >> "$TEST_STOP_LOG"')
  fake("osascript", 'printf "osascript %s\\n" "$*" >> "$TEST_DOCKER_LOG"')

  const pressure = invoke(
    {
      session_id: "pressure",
      cwd: repo,
      hook_event_name: "UserPromptSubmit",
      prompt: "계속",
    },
    {
      TEST_FREE_PERCENT: "10",
      TEST_SWAP_MB: "9000",
      TEST_STACKS: "supabase_db_other-a\nsupabase_db_other-b",
    },
  )
  assert.match(pressure.hookSpecificOutput.additionalContext, /RESOURCE_PRESSURE/)
  assert.match(pressure.hookSpecificOutput.additionalContext, /other-a,other-b/)

  const blocked = invoke(
    {
      session_id: "owner",
      cwd: repo,
      hook_event_name: "PreToolUse",
      tool_name: "Bash",
      tool_input: { command: "supabase start" },
    },
    { TEST_STACKS: "supabase_db_other-project" },
  )
  assert.equal(blocked.hookSpecificOutput.permissionDecision, "deny")

  const allowed = invoke({
    session_id: "owner",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "supabase start" },
  })
  assert.equal(allowed, null)
  assert.equal(readMarker("owner").owns ?? false, false, "pre-tool permission does not prove execution")
  invoke({
    session_id: "owner", cwd: repo, hook_event_name: "PostToolUse", tool_name: "Bash",
    tool_input: { command: "supabase start" }, tool_response: { stdout: "Started local development setup.", exit_code: 0 },
  }, { TEST_STACKS: "supabase_db_example-erp\nsupabase_db_other_example-erp" })
  assert.equal(readMarker("owner").owns, true)
  assert.deepEqual(readMarker("owner").supabaseContainerIds, [cid("supabase_db_example-erp")], "project labels distinguish overlapping name suffixes")

  invoke(
    {
      session_id: "observer",
      cwd: repo,
      hook_event_name: "UserPromptSubmit",
      prompt: "같은 프로젝트 계속",
    },
    { TEST_STACKS: "supabase_db_example-erp" },
  )
  invoke(
    {
      session_id: "owner",
      cwd: repo,
      hook_event_name: "SessionEnd",
      reason: "other",
    },
    { TEST_STACKS: "supabase_db_example-erp" },
  )
  assert.equal(readMarker("observer").owns, true)
  settle()
  assert.equal(fs.existsSync(stopLog), false)

  invoke(
    {
      session_id: "observer",
      cwd: repo,
      hook_event_name: "SessionEnd",
      reason: "other",
    },
    { TEST_STACKS: "supabase_db_example-erp" },
  )
  waitFor(() => /stop --project-id example-erp/.test(readLog(stopLog)), "supabase stop")

  fs.rmSync(probeLog, { force: true })
  const unrelated = invoke({
    session_id: "other-command",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "git status --short" },
  })
  assert.equal(unrelated, null)
  assert.equal(readLog(probeLog), "", "unrelated commands must not probe Docker or OS memory")

  // --- Docker 컨테이너 소유권 추적 ---
  fs.rmSync(dockerLog, { force: true })

  // 조회·정리 명령은 소유권 스냅샷을 열지 않는다.
  invoke({
    session_id: "docker-owner",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "docker compose down" },
  })
  assert.equal(readMarker("docker-owner").dockerPending ?? null, null)

  invoke({
    session_id: "docker-owner",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "docker run -d --name app-web nginx" },
  })
  assert.deepEqual(readMarker("docker-owner").dockerPending.before, [])

  invoke({
    session_id: "docker-owner", cwd: repo, hook_event_name: "PostToolUse", tool_name: "Bash",
    tool_input: { command: "docker run -d --name app-web nginx" }, tool_response: { stdout: cid("app-web"), exit_code: 0 },
  }, { TEST_STACKS: "app-web\nbystander" })
  assert.deepEqual(readMarker("docker-owner").dockerOwned, [cid("app-web")])

  invoke(
    {
      session_id: "docker-owner",
      cwd: repo,
      hook_event_name: "SessionEnd",
      reason: "other",
    },
    { TEST_STACKS: "app-web\nbystander" },
  )
  waitFor(() => readLog(dockerLog).includes(`docker stop -t 3 ${cid("app-web")}`), "docker stop")
  assert.equal(readLog(dockerLog).includes(cid("bystander")), false, "never stop concurrent bystanders")
  assert.doesNotMatch(readLog(dockerLog), /desktop stop/, "KEEP=1이면 앱을 종료하지 않는다")

  // --- 남은 컨테이너가 없을 때만 Docker Desktop을 내린다 ---
  fs.rmSync(dockerLog, { force: true })
  invoke({
    session_id: "quitter",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "docker run -d --name solo nginx" },
  })
  invoke(
    { session_id: "quitter", cwd: repo, hook_event_name: "PostToolUse", tool_name: "Bash",
      tool_input: { command: "docker run -d --name solo nginx" }, tool_response: { stdout: cid("solo"), exit_code: 0 } },
    { TEST_STACKS: "solo" },
  )
  invoke(
    { session_id: "quitter", cwd: repo, hook_event_name: "SessionEnd", reason: "other" },
    { TEST_STACKS: "solo", TEST_STACKS_AFTER: "", AGENT_DOCKER_GUARD_KEEP: "" },
  )
  waitFor(() => /desktop stop/.test(readLog(dockerLog)), "docker desktop stop")

  // 다른 컨테이너가 남아 있으면 앱을 유지한다.
  fs.rmSync(dockerLog, { force: true })
  invoke({
    session_id: "sharer",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "docker run -d --name mine nginx" },
  })
  invoke(
    { session_id: "sharer", cwd: repo, hook_event_name: "PostToolUse", tool_name: "Bash",
      tool_input: { command: "docker run -d --name mine nginx" }, tool_response: { stdout: cid("mine"), exit_code: 0 } },
    { TEST_STACKS: "mine\ntheirs" },
  )
  invoke(
    { session_id: "sharer", cwd: repo, hook_event_name: "SessionEnd", reason: "other" },
    { TEST_STACKS: "mine\ntheirs", TEST_STACKS_AFTER: "theirs", AGENT_DOCKER_GUARD_KEEP: "" },
  )
  waitFor(() => readLog(dockerLog).includes(`docker stop -t 3 ${cid("mine")}`), "docker stop mine")
  assert.equal(readLog(dockerLog).includes(cid("theirs")), false)
  settle()
  assert.doesNotMatch(readLog(dockerLog), /desktop stop/, "남의 컨테이너가 있으면 앱 유지")

  // Pending, failed, expired and legacy claims must never become ownership.
  for (const scenario of ["pending", "failed", "expired", "legacy", "compound", "compose", "mismatched-tool", "missing-result"]) {
    fs.rmSync(dockerLog, { force: true })
    const command = scenario === "compound" ? "docker run -d --name uncertain nginx; echo done"
      : scenario === "compose" ? "docker compose up -d" : "docker run -d --name uncertain nginx"
    invoke({ session_id: scenario, cwd: repo, hook_event_name: "PreToolUse", tool_name: "Bash", tool_use_id: "original", tool_input: { command } })
    const marker = readMarker(scenario)
    if (scenario === "expired") marker.dockerPending.at = 0
    if (scenario === "legacy") {
      marker.dockerOwned = ["uncertain"]
      marker.dockerPending = { before: [], at: Date.now() }
    }
    fs.writeFileSync(path.join(cache, "sessions", `${scenario}.json`), JSON.stringify(marker))
    if (["failed", "expired", "compound", "compose", "mismatched-tool", "missing-result"].includes(scenario)) {
      invoke({ session_id: scenario, cwd: repo, hook_event_name: "PostToolUse", tool_name: "Bash",
        tool_use_id: scenario === "mismatched-tool" ? "another" : "original",
        tool_input: { command }, tool_response: scenario === "missing-result" ? undefined : { stdout: cid("uncertain"), exit_code: scenario === "failed" ? 1 : 0 } },
        { TEST_STACKS: "uncertain\nbystander" })
    }
    invoke({ session_id: scenario, cwd: repo, hook_event_name: "SessionEnd" }, { TEST_STACKS: "uncertain\nbystander" })
    settle(100)
    assert.equal(readLog(dockerLog), "", `${scenario} must not authorize cleanup`)
  }

  // Explicit starts can own previously stopped IDs, never already-running targets.
  fs.rmSync(dockerLog, { force: true })
  const stopped = { name: "stopped", id: cid("stopped"), running: false }
  invoke({ session_id: "starter", cwd: repo, hook_event_name: "PreToolUse", tool_name: "Bash",
    tool_input: { command: "docker start stopped existing" } },
    { TEST_STACKS: "existing", TEST_INSPECT: JSON.stringify([stopped]) })
  invoke({ session_id: "starter", cwd: repo, hook_event_name: "PostToolUse", tool_name: "Bash",
    tool_input: { command: "docker start stopped existing" }, tool_response: { stdout: "stopped\nexisting", exit_code: 0 } },
    { TEST_STACKS: "stopped\nexisting" })
  assert.deepEqual(readMarker("starter").dockerOwned, [cid("stopped")])
  invoke({ session_id: "starter", cwd: repo, hook_event_name: "SessionEnd" }, { TEST_STACKS: "stopped\nexisting" })
  waitFor(() => readLog(dockerLog).includes(cid("stopped")), "stop explicitly started container")
  assert.equal(readLog(dockerLog).includes(cid("existing")), false)

  // Reusing a name with a different immutable ID cannot inherit ownership.
  fs.rmSync(dockerLog, { force: true })
  fs.writeFileSync(path.join(cache, "sessions", "replaced.json"), JSON.stringify({
    ownershipVersion: 2, dockerOwned: ["a".repeat(64)], lastSeenAt: Date.now(),
  }))
  invoke({ session_id: "replaced", cwd: repo, hook_event_name: "SessionEnd" }, { TEST_STACKS: "replacement" })
  settle(100)
  assert.equal(readLog(dockerLog), "")

  // A replaced Supabase stack is not the stack this session started.
  fs.writeFileSync(path.join(cache, "sessions", "replaced-stack.json"), JSON.stringify({
    ownershipVersion: 2, owns: true, root: repo, projectId: "replaced-stack",
    supabaseContainerIds: ["b".repeat(64)], lastSeenAt: Date.now(),
  }))
  fs.rmSync(stopLog, { force: true })
  invoke({ session_id: "replaced-stack", cwd: repo, hook_event_name: "SessionEnd" }, { TEST_STACKS: "supabase_db_replaced-stack" })
  settle(100)
  assert.equal(readLog(stopLog), "")

  // Native Codex returns plain text, not an object containing an exit status.
  for (const kind of ["run", "create"]) {
    const name = `native-${kind}`
    const command = `docker ${kind} --name ${name} nginx`
    invoke({ session_id: name, cwd: repo, hook_event_name: "PreToolUse", tool_name: "Bash",
      tool_use_id: name, tool_input: { command } })
    invoke({ session_id: name, cwd: repo, hook_event_name: "PostToolUse", tool_name: "Bash",
      tool_use_id: name, tool_input: { command }, tool_response: `${cid(name)}\n` }, { TEST_STACKS: `${name}\nbystander` })
    assert.deepEqual(readMarker(name).dockerOwned, [cid(name)], "a raw immutable container ID is attributable")
    fs.rmSync(dockerLog, { force: true })
    invoke({ session_id: name, cwd: repo, hook_event_name: "SessionEnd" }, { TEST_STACKS: `${name}\nbystander` })
    waitFor(() => readLog(dockerLog).includes(cid(name)), `native ${kind} cleanup`)
    assert.equal(readLog(dockerLog).includes(cid("bystander")), false)
  }

  const nativeUnknown = [
    ["run-error", "docker run --name native-unknown nginx", "Error response from daemon: container name is already in use"],
    ["run-truncated", "docker run --name native-unknown nginx", cid("native-unknown").slice(0, 20)],
    ["run-unverified-id", "docker run --name native-unknown nginx", "f".repeat(64)],
    ["start-text", "docker start native-unknown", "native-unknown"],
    ["start-id", "docker start native-unknown", cid("native-unknown")],
    ["supabase-text", "supabase start", "Started local development setup."],
  ]
  for (const [name, command, response] of nativeUnknown) {
    invoke({ session_id: name, cwd: repo, hook_event_name: "PreToolUse", tool_name: "Bash",
      tool_use_id: name, tool_input: { command } }, {
      TEST_INSPECT: JSON.stringify([{ name: "native-unknown", id: cid("native-unknown"), running: false }]),
    })
    invoke({ session_id: name, cwd: repo, hook_event_name: "PostToolUse", tool_name: "Bash",
      tool_use_id: name, tool_input: { command }, tool_response: response },
      { TEST_STACKS: "native-unknown\nsupabase_db_example-erp" })
    const marker = readMarker(name)
    assert.deepEqual(marker.dockerOwned || [], [], `${name}: text does not establish ownership`)
    assert.equal(Boolean(marker.owns), false, `${name}: no unverified Supabase ownership`)
    fs.rmSync(dockerLog, { force: true })
    fs.rmSync(stopLog, { force: true })
    invoke({ session_id: name, cwd: repo, hook_event_name: "SessionEnd" },
      { TEST_STACKS: "native-unknown\nsupabase_db_example-erp" })
    settle(100)
    assert.equal(readLog(dockerLog), "", `${name}: no cleanup`)
    assert.equal(readLog(stopLog), "", `${name}: no stack cleanup`)
  }

  process.stdout.write("dev-resource-guard: 29 scenarios passed\n")
} finally {
  fs.rmSync(temp, { recursive: true, force: true })
}

function readMarker(id) {
  return JSON.parse(fs.readFileSync(path.join(cache, "sessions", `${id}.json`), "utf8"))
}
