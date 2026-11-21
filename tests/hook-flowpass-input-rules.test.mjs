import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import test from "node:test"
import { execFileSync } from "node:child_process"

const hook = path.resolve("hooks", "flowpass-input-rules.mjs")
const rules = fs.readFileSync(path.resolve("global", "flowpass-input-rules.md"), "utf8").trim()
const CLAUDE_WRITE = "mcp__plugin_flowpass_flowpass__flowpass_write"
const SECOND = 1000
const MINUTE = 60 * SECOND

function tempHome(t) {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), "flowpass-rules-"))
  t.after(() => fs.rmSync(home, { recursive: true, force: true }))
  return home
}

function run(home, input, script = hook) {
  const out = execFileSync("node", [script], { input: JSON.stringify(input), env: { ...process.env, HOME: home }, encoding: "utf8" })
  return out ? JSON.parse(out) : null
}

const reason = output => output?.hookSpecificOutput?.permissionDecisionReason

function stateFile(home, session) {
  return path.join(home, ".local", "state", "ai-working", "flowpass-input-rules", `${session}.json`)
}

// Move recorded deliveries into the past instead of sleeping.
function age(home, session, ms) {
  const state = JSON.parse(fs.readFileSync(stateFile(home, session), "utf8"))
  for (const entry of Object.values(state)) entry.at -= ms
  fs.writeFileSync(stateFile(home, session), JSON.stringify(state))
}

test("the first input call of a request is held with the full rules, the retry runs", t => {
  const home = tempHome(t)
  const call = { session_id: "s1", prompt_id: "p1", tool_name: CLAUDE_WRITE, tool_input: { dryRun: true } }
  const held = run(home, call)
  assert.equal(held.hookSpecificOutput.hookEventName, "PreToolUse")
  assert.equal(held.hookSpecificOutput.permissionDecision, "deny")
  assert.ok(reason(held).includes(rules))
  assert.match(reason(held), /다시 호출하면 실행된다/)
  age(home, "s1", 5 * SECOND)
  assert.equal(run(home, call), null)
  assert.equal(run(home, { ...call, tool_name: "mcp__plugin_flowpass_flowpass__flowpass_week" }), null)
})

test("every new request is held again", t => {
  const home = tempHome(t)
  const call = { session_id: "s2", prompt_id: "p1", tool_name: CLAUDE_WRITE }
  run(home, call)
  age(home, "s2", 5 * SECOND)
  assert.equal(run(home, call), null)
  assert.ok(reason(run(home, { ...call, prompt_id: "p2" })).includes(rules))
})

test("lookups and other tools pass without a record", t => {
  const home = tempHome(t)
  for (const tool_name of ["mcp__plugin_flowpass_flowpass__flowpass_status", "mcp__plugin_flowpass_flowpass__flowpass_read",
    "mcp__flowpass__flowpass_start", "mcp__flowpass__flowpass_feedback_list", "Bash", "mcp__other__write"]) {
    assert.equal(run(home, { session_id: "s3", prompt_id: "p1", tool_name }), null)
  }
  assert.equal(fs.existsSync(stateFile(home, "s3")), false)
})

test("a call issued alongside the held one is held too, without repeating the rules", t => {
  const home = tempHome(t)
  const call = { session_id: "s4", prompt_id: "p1", tool_name: CLAUDE_WRITE }
  run(home, call)
  const sibling = run(home, { ...call, tool_name: "mcp__plugin_flowpass_flowpass__flowpass_schedule" })
  assert.equal(sibling.hookSpecificOutput.permissionDecision, "deny")
  assert.equal(reason(sibling).includes(rules), false)
  // A retry reaches the hook about two seconds after the hold and must not be held again.
  age(home, "s4", 2 * SECOND)
  assert.equal(run(home, call), null)
})

test("Codex server naming and turn ids work the same way", t => {
  const home = tempHome(t)
  const call = { session_id: "s5", turn_id: "t1", tool_name: "mcp__flowpass__flowpass_file_put" }
  assert.ok(reason(run(home, call)).includes(rules))
  age(home, "s5", 5 * SECOND)
  assert.equal(run(home, call), null)
  assert.ok(reason(run(home, { ...call, turn_id: "t2" })).includes(rules))
})

test("a subagent gets its own delivery", t => {
  const home = tempHome(t)
  const call = { session_id: "s6", prompt_id: "p1", tool_name: CLAUDE_WRITE }
  run(home, call)
  age(home, "s6", 5 * SECOND)
  assert.equal(run(home, call), null)
  assert.ok(reason(run(home, { ...call, agent_id: "agent-1" })).includes(rules))
})

test("long requests and runtimes without a request id get the rules again after ten minutes", t => {
  const home = tempHome(t)
  const call = { session_id: "s7", tool_name: CLAUDE_WRITE }
  run(home, call)
  age(home, "s7", 9 * MINUTE)
  assert.equal(run(home, call), null)
  age(home, "s7", 2 * MINUTE)
  assert.ok(reason(run(home, call)).includes(rules))
})

test("a missing rules file lets the call through with a warning", t => {
  const home = tempHome(t)
  const copy = path.join(home, "hooks", "flowpass-input-rules.mjs")
  fs.mkdirSync(path.dirname(copy))
  fs.copyFileSync(hook, copy)
  const output = run(home, { session_id: "s8", prompt_id: "p1", tool_name: CLAUDE_WRITE }, copy)
  assert.equal(output.hookSpecificOutput, undefined)
  assert.match(output.systemMessage, /규칙 파일을 읽지 못해/)
})

test("the hook is registered for both runtimes and the rules file is linked next to it", () => {
  const manifest = JSON.parse(fs.readFileSync(path.resolve("global", "governance-hooks.json"), "utf8"))
  const record = manifest.hooks.PreToolUse.find(item => item.hooks.some(h => h.command.endsWith("/flowpass-input-rules.mjs")))
  const matcher = new RegExp(record.matcher)
  assert.ok(matcher.test(CLAUDE_WRITE))
  assert.ok(matcher.test("mcp__flowpass__flowpass_write"))
  assert.equal(matcher.test("Bash"), false)
  const links = JSON.parse(fs.readFileSync(path.resolve("manifest.json"), "utf8")).links
  assert.ok(links.some(link => link.repo === "global/flowpass-input-rules.md" && link.target === "~/.claude/hooks/flowpass-input-rules.md"))
})
