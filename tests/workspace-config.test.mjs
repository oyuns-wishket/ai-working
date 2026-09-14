import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import { execFileSync, spawnSync } from "node:child_process"
import test from "node:test"
import { readWorkspaceConfig, matchWorkspace } from "../hooks/workspace-config.mjs"

function fixture(t) {
  const home = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "workspace-config-")))
  t.after(() => fs.rmSync(home, { recursive: true, force: true }))
  const configDir = path.join(home, ".config", "ai-working")
  fs.mkdirSync(configDir, { recursive: true })
  const env = { ...process.env, HOME: home, XDG_CONFIG_HOME: path.join(home, ".config") }
  delete env.AI_WORKING_PROJECTS_ROOT
  delete env.AI_WORKING_WORKSPACES_CONFIG
  const write = settings => fs.writeFileSync(path.join(configDir, "workspaces.json"), JSON.stringify({ schema_version: 1, ...settings }))
  return { home, env, write }
}

test("multiple roots, spaces, path boundaries, and exclusions", t => {
  const { home, env, write } = fixture(t)
  write({ workspace_roots: ["~/work one", "~/work-two"], excluded_roots: ["~/work-two/policy"] })
  const config = readWorkspaceConfig(env)
  assert.equal(matchWorkspace(path.join(home, "work one", "project", "src.py"), config, env), path.join(home, "work one"))
  assert.equal(matchWorkspace(path.join(home, "work-two", "project"), config, env), path.join(home, "work-two"))
  assert.equal(matchWorkspace(path.join(home, "work-two-other", "project"), config, env), null)
  assert.equal(matchWorkspace(path.join(home, "work-two", "policy", "src.py"), config, env), null)
})

test("legacy env overrides config; explicit empty roots disables matching", t => {
  const { home, env, write } = fixture(t)
  assert.equal(readWorkspaceConfig(env).source, "legacy-default")
  write({ workspace_roots: [] })
  assert.equal(matchWorkspace(path.join(home, "aidp", "project"), readWorkspaceConfig(env), env), null)
  const legacy = { ...env, AI_WORKING_PROJECTS_ROOT: path.join(home, "legacy") }
  assert.deepEqual(readWorkspaceConfig(legacy).workspace_roots, [path.join(home, "legacy")])
})

test("symlink escape stays outside, linked worktrees inherit repository ownership", t => {
  const { home, env, write } = fixture(t)
  const root = path.join(home, "projects")
  const repo = path.join(root, "app")
  const outside = path.join(home, "outside")
  fs.mkdirSync(repo, { recursive: true })
  fs.mkdirSync(outside)
  fs.symlinkSync(outside, path.join(root, "escape"))
  write({ workspace_roots: [root] })
  let config = readWorkspaceConfig(env)
  assert.equal(matchWorkspace(path.join(root, "escape", "new.py"), config, env), null)
  execFileSync("git", ["init", "-q", "-b", "main", repo])
  execFileSync("git", ["-C", repo, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "--allow-empty", "-qm", "initial"])
  const worktree = path.join(home, "temp-worktree")
  execFileSync("git", ["-C", repo, "worktree", "add", "-qb", "feat/test", worktree])
  assert.equal(matchWorkspace(worktree, config, env), root)
  write({ workspace_roots: [root], excluded_roots: [repo] })
  config = readWorkspaceConfig(env)
  assert.equal(matchWorkspace(worktree, config, env), null)
})

test("invalid configuration is reported instead of silently widening the workspace", t => {
  const { home, env, write } = fixture(t)
  write({ workspace_roots: ["relative/path"] })
  assert.throws(() => readWorkspaceConfig(env), /absolute/)
  const result = spawnSync(process.execPath, ["scripts/check_environment.mjs", "--project", home, "--json"], { env, encoding: "utf8" })
  assert.equal(result.status, 2)
  assert.equal(JSON.parse(result.stdout).status, "error")
})

test("doctor measures handoff size without mutating the source or configuration", t => {
  const { home, env, write } = fixture(t)
  const project = path.join(home, "projects", "app")
  const handoff = path.join(project, "docs", "handoff", "HANDOFF.md")
  fs.mkdirSync(path.dirname(handoff), { recursive: true })
  const content = "# Handoff\n" + "old history\n".repeat(2000)
  fs.writeFileSync(handoff, content)
  write({ workspace_roots: [path.join(home, "projects")] })
  const result = spawnSync(process.execPath, ["scripts/check_environment.mjs", "--project", project, "--json"], { env, encoding: "utf8" })
  assert.equal(result.status, 0)
  const report = JSON.parse(result.stdout)
  assert.equal(report.projects[0].handoff_exceeds_context_budget, true)
  assert.equal(report.projects[0].handoff_source_bytes, Buffer.byteLength(content))
  assert.equal(fs.readFileSync(handoff, "utf8"), content)
})
