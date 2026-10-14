import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import { execFileSync } from "node:child_process"
import test from "node:test"
import { isShortKoreanTitle, paseoTitleNotice } from "../hooks/paseo-title.mjs"

const NOW = Date.parse("2026-01-01T00:10:00Z")

function fixture(t, { workspace = {}, agent = {}, paseoJson } = {}) {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "paseo-title-"))
  t.after(() => fs.rmSync(temp, { recursive: true, force: true }))
  const home = path.join(temp, "paseo")
  const project = path.join(temp, "프로젝트")
  const bin = path.join(temp, "bin")
  fs.mkdirSync(bin)
  fs.writeFileSync(path.join(bin, "paseo"), "#!/bin/sh\n", { mode: 0o755 })
  fs.mkdirSync(path.join(home, "agents", "some-dir"), { recursive: true })
  fs.mkdirSync(path.join(home, "projects"))
  fs.mkdirSync(project)
  if (paseoJson) fs.writeFileSync(path.join(project, "paseo.json"), JSON.stringify(paseoJson))
  fs.writeFileSync(path.join(home, "agents", "some-dir", "agent-1.json"), JSON.stringify({
    id: "agent-1", workspaceId: "wks_1", title: "Fix the login test", internal: false, ...agent,
  }))
  fs.writeFileSync(path.join(home, "projects", "workspaces.json"), JSON.stringify([{
    workspaceId: "wks_1", cwd: project, worktreeRoot: project, mainRepoRoot: null, isPaseoOwnedWorktree: false,
    title: "Fix the login test", createdAt: "2026-01-01T00:09:00Z", ...workspace,
  }]))
  return { env: { PASEO_AGENT_ID: "agent-1", PASEO_HOME: home, PATH: bin }, home, project }
}

test("short Korean titles are recognised by character count", () => {
  assert.ok(isShortKoreanTitle("현금영수증 취소"))
  assert.ok(isShortKoreanTitle("KPI 화면 분석"))
  assert.ok(!isShortKoreanTitle("발행 연동 체크리스트"))
  assert.ok(!isShortKoreanTitle("Fix login"))
  assert.ok(!isShortKoreanTitle(null))
})

test("a fresh workspace without title instructions gets the exact CLI rename command", t => {
  const { env } = fixture(t)
  const notice = paseoTitleNotice(env, NOW)
  assert.match(notice, /`paseo workspace rename wks_1 "<제목>"`/)
  assert.doesNotMatch(notice, /MCP/)
})

test("stays silent when the paseo CLI is not on PATH", t => {
  const { env } = fixture(t)
  assert.equal(paseoTitleNotice({ ...env, PATH: path.join(path.dirname(env.PATH), "empty") }, NOW), "")
})

test("a placeholder copied from the first prompt still asks for a rename", t => {
  const { env } = fixture(t, { workspace: { title: "제목 바꿔줘" }, agent: { title: "제목 바꿔줘" } })
  assert.match(paseoTitleNotice(env, NOW), /paseo workspace rename wks_1/)
})

test("stays silent when nothing needs to change", async t => {
  const instructions = { metadataGeneration: { title: { instructions: "짧게" } } }
  const cases = {
    "repository carries the instructions": { paseoJson: instructions },
    "title is already short Korean": { workspace: { title: "로그인 복구" } },
    "workspace is not new": { workspace: { createdAt: "2025-12-31T00:00:00Z" } },
    "agent is internal": { agent: { internal: true } },
    "agent has no workspace": { agent: { workspaceId: null } },
    "workspace id is not a plain identifier": { agent: { workspaceId: "wks_1; rm -rf /" } },
  }
  for (const [name, options] of Object.entries(cases)) {
    await t.test(name, t => assert.equal(paseoTitleNotice(fixture(t, options).env, NOW), ""))
  }
  await t.test("outside Paseo", () => assert.equal(paseoTitleNotice({}, NOW), ""))
  await t.test("unreadable registry", t => {
    const { env, home } = fixture(t)
    fs.writeFileSync(path.join(home, "projects", "workspaces.json"), "{broken")
    assert.equal(paseoTitleNotice(env, NOW), "")
  })
})

test("a Paseo-owned worktree reads the instructions from the main repository", t => {
  const { env, project } = fixture(t, { paseoJson: { metadataGeneration: { title: { instructions: "짧게" } } } })
  const file = path.join(env.PASEO_HOME, "projects", "workspaces.json")
  const [workspace] = JSON.parse(fs.readFileSync(file, "utf8"))
  fs.writeFileSync(file, JSON.stringify([{ ...workspace, isPaseoOwnedWorktree: true, mainRepoRoot: project, worktreeRoot: "/nonexistent", cwd: "/nonexistent" }]))
  assert.equal(paseoTitleNotice(env, NOW), "")
})

test("the session entry hook includes the notice without writing anything", t => {
  const { env, home, project } = fixture(t, { workspace: { createdAt: new Date().toISOString() } })
  const before = fs.readdirSync(project)
  const out = execFileSync("node", [path.resolve("hooks/session-entry.mjs")], {
    cwd: project, env: { ...process.env, ...env, PATH: `${env.PATH}${path.delimiter}${process.env.PATH}`, HOME: path.dirname(home) },
    input: JSON.stringify({ cwd: project }), encoding: "utf8", timeout: 20000,
  })
  assert.match(JSON.parse(out).hookSpecificOutput.additionalContext, /\[Paseo 제목\]/)
  assert.deepEqual(fs.readdirSync(project), before)
})
