import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import { createHash } from "node:crypto"
import { execFileSync } from "node:child_process"
import test from "node:test"
import { MAX_CONTEXT_BYTES, readHandoffContext } from "../hooks/handoff-context.mjs"

const repo = path.resolve(".")

function fixture(t, content, installed = false) {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "handoff-context-"))
  t.after(() => fs.rmSync(temp, { recursive: true, force: true }))
  const home = path.join(temp, "home")
  const project = path.join(temp, "프로젝트")
  const hooks = path.join(home, ".claude", "hooks")
  const bin = path.join(temp, "bin")
  fs.mkdirSync(hooks, { recursive: true })
  fs.mkdirSync(bin)
  fs.mkdirSync(path.join(project, "docs", "handoff"), { recursive: true })
  fs.writeFileSync(path.join(home, ".claude", ".disk-stamp"), "")
  fs.writeFileSync(path.join(bin, "gh"), "#!/bin/sh\nexit 0\n", { mode: 0o755 })
  execFileSync("git", ["init", "-q"], { cwd: project })
  execFileSync("git", ["remote", "add", "origin", "https://example.invalid/test/repo.git"], { cwd: project })
  const file = path.join(project, "docs", "handoff", "HANDOFF.md")
  if (content !== null) fs.writeFileSync(file, content)
  if (installed) {
    for (const name of ["session-start.sh", "lib.sh", "handoff-context.mjs"]) {
      fs.copyFileSync(path.join(repo, "hooks", name), path.join(hooks, name))
    }
  }
  return {
    file, hooks,
    run() {
      const hook = path.join(installed ? hooks : path.join(repo, "hooks"), "session-start.sh")
      const result = execFileSync("/bin/sh", [hook], {
        cwd: project,
        env: { ...process.env, HOME: home, PATH: `${bin}:${process.env.PATH}` },
        input: JSON.stringify({ cwd: project }), encoding: "utf8", timeout: 10000,
      })
      return result.trim() ? JSON.parse(result).hookSpecificOutput.additionalContext : ""
    },
  }
}

test("source hook selects current sections and preserves the original file", t => {
  const setup = fixture(t, "# Handoff\nPRIVATE_OLD_DETAIL\n## Next actions\nold action\n## Done\ncompleted content\n## Next actions\ncurrent action\n### Detail\nneeded detail\n## Open items & blockers\ncurrent blocker\n## Decisions & context\ncurrent decision\n## Archive\nARCHIVE_DETAIL\n")
  const hash = () => createHash("sha256").update(fs.readFileSync(setup.file)).digest("hex")
  const before = hash()
  const context = setup.run()
  assert.match(context, /source: docs\/handoff\/HANDOFF.md/)
  for (const text of ["current action", "needed detail", "current blocker", "current decision"]) assert.ok(context.includes(text))
  for (const text of ["old action", "PRIVATE_OLD_DETAIL", "completed content", "ARCHIVE_DETAIL"]) assert.ok(!context.includes(text))
  assert.equal(hash(), before)
})

test("installed hook handles multilingual content within a UTF-8 byte budget", t => {
  const setup = fixture(t, `## 다음 작업\n우선 작업\n${"해야 할 일 🛠️\n".repeat(3000)}## 미해결 항목 및 블로커\n막힌 작업\n${"확인 대기\n".repeat(1000)}## 결정 사항 및 맥락\n결정 기록\n${"설명\n".repeat(1000)}`, true)
  const context = setup.run()
  assert.ok(Buffer.byteLength(context) <= MAX_CONTEXT_BYTES)
  for (const text of ["우선 작업", "막힌 작업", "결정 기록", "[truncated]"]) assert.ok(context.includes(text))
  assert.ok(!context.includes("\ufffd"))
})

test("huge single lines cannot consume the output or hide subsequent sections", t => {
  const setup = fixture(t, `## Next actions\n${"가".repeat(400000)}\n## Open items & blockers\nvisible blocker\n## Decisions & context\nvisible decision\n`)
  const context = setup.run()
  assert.ok(Buffer.byteLength(context) <= MAX_CONTEXT_BYTES)
  assert.match(context, /visible blocker/)
  assert.match(context, /visible decision/)
  assert.match(context, /truncated/)
  assert.ok(!context.includes("\ufffd"))
})

test("fenced fake headings are never selected as real sections", t => {
  const setup = fixture(t, "# Notes\n```markdown\n## Next actions\nFAKE_ACTION\n```\n~~~md\n## Open items & blockers\nFAKE_BLOCKER\n~~~\n## Next actions\nreal action\n## Decisions & context\nreal decision\n")
  const context = setup.run()
  assert.match(context, /real action/)
  assert.match(context, /real decision/)
  assert.doesNotMatch(context, /FAKE_/)
})

test("missing, empty, and unrecognized documents fail open without a raw fallback", t => {
  const missing = fixture(t, null)
  const notice = missing.run()
  assert.match(notice, /\[인계 없음\] docs\/handoff\/HANDOFF.md/)
  assert.ok(Buffer.byteLength(notice) < 512)
  assert.match(readHandoffContext(missing.file), /unavailable/)
  for (const content of ["", "# Archive\nDO_NOT_INJECT\n", "##Next actions\nDO_NOT_INJECT\n", "```\n## Next actions\nDO_NOT_INJECT\n"]) {
    const setup = fixture(t, content)
    const context = setup.run()
    assert.match(context, /No recognized current sections/)
    assert.doesNotMatch(context, /DO_NOT_INJECT/)
  }
})

test("missing installed helper produces a concise skipped notice", t => {
  const setup = fixture(t, "## Next actions\nDO_NOT_INJECT\n", true)
  fs.unlinkSync(path.join(setup.hooks, "handoff-context.mjs"))
  const context = setup.run()
  assert.match(context, /bounded reader unavailable/)
  assert.doesNotMatch(context, /DO_NOT_INJECT/)
  assert.ok(Buffer.byteLength(context) < 512)
})

test("oversized files have bounded scans and disclose possibly missing later sections", t => {
  const setup = fixture(t, `## Next actions\nfirst action\n## Archive\n${"history\n".repeat(650000)}## Next actions\nAFTER_SCAN_LIMIT\n`)
  const context = setup.run()
  assert.match(context, /first action/)
  assert.match(context, /Scan capped at 4 MiB|Scan time budget reached/)
  assert.match(context, /later sections may be missing or newer/)
  assert.doesNotMatch(context, /AFTER_SCAN_LIMIT/)
  assert.ok(Buffer.byteLength(context) <= MAX_CONTEXT_BYTES)
})

test("a single recognized section can use the available budget", t => {
  const setup = fixture(t, `## Next actions\n${"next action\n".repeat(1200)}`)
  const context = setup.run()
  assert.ok(Buffer.byteLength(context) > 7000)
  assert.ok(Buffer.byteLength(context) <= MAX_CONTEXT_BYTES)
  assert.match(context, /truncated/)
})

test("unused blocker and decision space is reassigned to actions", t => {
  const setup = fixture(t, `## Next actions\n${"next action\n".repeat(1200)}## Open items & blockers\nnone\n## Decisions & context\nkeep existing behavior\n`)
  const context = setup.run()
  assert.ok(Buffer.byteLength(context) > 7000)
  assert.ok(Buffer.byteLength(context) <= MAX_CONTEXT_BYTES)
  assert.match(context, /keep existing behavior/)
})

test("standalone reader rejects a FIFO without waiting for a writer", t => {
  const setup = fixture(t, null)
  execFileSync("mkfifo", [setup.file])
  const context = execFileSync("node", [path.join(repo, "hooks", "handoff-context.mjs"), setup.file], {
    encoding: "utf8", timeout: 2000,
  })
  assert.match(context, /unavailable/)
})

test("Korean action/context/blocker aliases normalize separator spacing", t => {
  const setup = fixture(t, "## 다음   액션\ncurrent action\n## 결정/컨텍스트\ncurrent decision\n## 미해결  /블로커\ncurrent blocker\n")
  const context = setup.run()
  for (const text of ["current action", "current decision", "current blocker"]) assert.ok(context.includes(text))
  assert.ok(context.indexOf("current action") < context.indexOf("current blocker"))
})

test("explicit historical subtrees are omitted until the next sibling or ancestor", t => {
  const setup = fixture(t, "## 다음 액션\ncurrent action\n### (이전)\nOLD_KOREAN\n#### Next actions\nNESTED_OLD_ACTION\n```md\n### False sibling\n```\nSTILL_OLD\n### Current follow-up\nactive follow-up\n### History\nOLD_ENGLISH\n#### Details\nOLD_DETAILS\n### Current checks\nactive check\n### Completed\nOLD_COMPLETED\n## 미해결 / 블로커\ncurrent blocker\n## 결정 / 컨텍스트\ncurrent decision\n")
  const context = setup.run()
  for (const text of ["current action", "active follow-up", "active check", "current blocker", "current decision"]) assert.ok(context.includes(text))
  assert.doesNotMatch(context, /OLD_|NESTED_OLD|STILL_OLD|False sibling|### History|### Completed|### \(이전\)/)
})

test("global archived copies cannot override current canonical sections", t => {
  const setup = fixture(t, "# Handoff\n## Next actions\nCURRENT_ACTION\n## Open items & blockers\nCURRENT_BLOCKER\n## Decisions & context\nCURRENT_DECISION\n## Archive\n### 2025-01-01\n#### Next actions\nOLD_ACTION\n#### Open items & blockers\nOLD_BLOCKER\n#### Decisions & context\nOLD_DECISION\n")
  const context = setup.run()
  for (const text of ["CURRENT_ACTION", "CURRENT_BLOCKER", "CURRENT_DECISION"]) assert.ok(context.includes(text))
  assert.doesNotMatch(context, /OLD_/)
})

test("shallower canonical sections take priority over nested same-title sections", t => {
  const setup = fixture(t, "# Handoff\n## Example\n#### Next actions\nNESTED_BEFORE\n## Next actions\nCANONICAL_ACTION\n## Notes\n#### Next actions\nNESTED_AFTER\n")
  const context = setup.run()
  assert.match(context, /CANONICAL_ACTION/)
  assert.doesNotMatch(context, /NESTED_/)
})

test("pathological tiny lines have an internal scan deadline", t => {
  const setup = fixture(t, `## Next actions\ncurrent action\n${"\n".repeat(4 * 1024 * 1024)}`)
  const context = setup.run()
  assert.match(context, /current action/)
  assert.match(context, /Scan time budget reached|Scan capped/)
  assert.ok(Buffer.byteLength(context) <= MAX_CONTEXT_BYTES)
})

function wikiRegistry(t, setup, projects) {
  const home = path.dirname(path.dirname(setup.hooks))
  const skills = path.join(home, ".claude", "skills")
  fs.mkdirSync(skills, { recursive: true })
  fs.symlinkSync(path.join(repo, "skills", "project-wiki-context"), path.join(skills, "project-wiki-context"))
  const wiki = path.join(home, "wiki")
  fs.mkdirSync(path.join(wiki, ".system", "registry"), { recursive: true })
  fs.writeFileSync(path.join(wiki, ".system", "knowledge-contract.json"), JSON.stringify({ schema_version: 2, paths: {
    canonical: "sys-wiki", candidate: "candidate", manual: "my-wiki",
    registry: ".system/registry/project-registry.json", registry_schema: ".system/registry/project-registry.schema.json",
    schema: ".system/schemas/canonical-note.schema.json", template: ".system/templates/canonical-note.md" } }))
  fs.writeFileSync(path.join(wiki, ".system", "registry", "project-registry.json"), JSON.stringify({ schema_version: 2, projects }))
  return wiki
}

test("unregistered repositories get one bounded wiki notice; missing resolver stays silent", t => {
  const silent = fixture(t, "## Next actions\ncurrent action\n", true)
  assert.doesNotMatch(silent.run(), /wiki 미연결/)
  const setup = fixture(t, "## Next actions\ncurrent action\n", true)
  const wiki = wikiRegistry(t, setup, [])
  process.env.AI_WORKING_CONTEXT_REGISTRY_PATH = wiki
  t.after(() => { delete process.env.AI_WORKING_CONTEXT_REGISTRY_PATH })
  const context = setup.run()
  assert.match(context, /current action/)
  assert.match(context, /\[wiki 미연결\] remote example.invalid\/test\/repo/)
  assert.match(context, /connect_project_wiki.py --personal/)
  assert.ok(Buffer.byteLength(context) <= MAX_CONTEXT_BYTES + 1024)
  process.env.AI_WORKING_STARTUP_WIKI = "0"
  t.after(() => { delete process.env.AI_WORKING_STARTUP_WIKI })
  assert.doesNotMatch(setup.run(), /wiki 미연결/)
})

test("registered repositories produce no wiki notice", t => {
  const setup = fixture(t, "## Next actions\ncurrent action\n", true)
  const wiki = wikiRegistry(t, setup, [{ id: "example.invalid/test/repo", canonical_remote: "https://example.invalid/test/repo",
    remote_aliases: [], local_aliases: [], connection_status: "common-only", lifecycle: "active", project_kind: "managed-project",
    security_domain: "work", wiki_namespace: null, retrieval_profile: "common-only", customer_scope: "common",
    canonical_write_target: null, read_scopes: [], manual_read_bindings: [] }])
  process.env.AI_WORKING_CONTEXT_REGISTRY_PATH = wiki
  t.after(() => { delete process.env.AI_WORKING_CONTEXT_REGISTRY_PATH })
  const context = setup.run()
  assert.match(context, /current action/)
  assert.doesNotMatch(context, /wiki 미연결/)
})
