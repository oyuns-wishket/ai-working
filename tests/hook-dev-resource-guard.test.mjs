import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import { execFileSync } from "node:child_process"

const script = path.resolve("hooks/dev-resource-guard.mjs")
const temp = fs.mkdtempSync(path.join(os.tmpdir(), "dev-resource-guard-test-"))
const repo = path.join(temp, "example-erp")
const bin = path.join(temp, "bin")
const cache = path.join(temp, "cache")
const stopLog = path.join(temp, "supabase-stop.log")
const dockerLog = path.join(temp, "docker.log")

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

  fake("memory_pressure", 'printf "System-wide memory free percentage: %s%%\\n" "$TEST_FREE_PERCENT"')
  fake("sysctl", 'printf "vm.swapusage: total = 10240.00M used = %sM free = 0.00M\\n" "$TEST_SWAP_MB"')
  fake(
    "docker",
    [
      'case "$1" in',
      '  ps)',
      '    if [ "$2" = "-q" ]; then printf "%s\\n" "$TEST_STACKS_AFTER"; else printf "%s\\n" "$TEST_STACKS"; fi',
      '    ;;',
      '  *) printf "docker %s\\n" "$*" >> "$TEST_DOCKER_LOG" ;;',
      'esac',
    ].join("\n"),
  )
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
  assert.equal(readMarker("owner").owns, true)

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

  const unrelated = invoke({
    session_id: "other-command",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "npm test" },
  })
  assert.equal(unrelated, null)

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

  invoke(
    {
      session_id: "docker-owner",
      cwd: repo,
      hook_event_name: "UserPromptSubmit",
      prompt: "계속",
    },
    { TEST_STACKS: "app-web" },
  )
  assert.deepEqual(readMarker("docker-owner").dockerOwned, ["app-web"])

  invoke(
    {
      session_id: "docker-owner",
      cwd: repo,
      hook_event_name: "SessionEnd",
      reason: "other",
    },
    { TEST_STACKS: "app-web" },
  )
  waitFor(() => /docker stop -t 3 app-web/.test(readLog(dockerLog)), "docker stop")
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
    { session_id: "quitter", cwd: repo, hook_event_name: "UserPromptSubmit", prompt: "계속" },
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
    { session_id: "sharer", cwd: repo, hook_event_name: "UserPromptSubmit", prompt: "계속" },
    { TEST_STACKS: "mine\ntheirs" },
  )
  invoke(
    { session_id: "sharer", cwd: repo, hook_event_name: "SessionEnd", reason: "other" },
    { TEST_STACKS: "mine\ntheirs", TEST_STACKS_AFTER: "theirs", AGENT_DOCKER_GUARD_KEEP: "" },
  )
  waitFor(() => /docker stop -t 3 mine/.test(readLog(dockerLog)), "docker stop mine")
  settle()
  assert.doesNotMatch(readLog(dockerLog), /desktop stop/, "남의 컨테이너가 있으면 앱 유지")

  process.stdout.write("dev-resource-guard: 10 scenarios passed\n")
} finally {
  fs.rmSync(temp, { recursive: true, force: true })
}

function readMarker(id) {
  return JSON.parse(fs.readFileSync(path.join(cache, "sessions", `${id}.json`), "utf8"))
}
