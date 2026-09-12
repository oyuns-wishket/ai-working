import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import test from "node:test"
import { execFileSync, spawnSync } from "node:child_process"

const repo = path.resolve(".")
const script = path.join(repo, "bootstrap.sh")

function run(target, ...args) {
  return execFileSync("/bin/bash", [script, "--target-root", target, ...args], {
    cwd: repo,
    encoding: "utf8",
    env: { ...process.env, NO_COLOR: "1" },
  })
}

function memoryPath(target) {
  const slug = target.replaceAll("/", "-")
  return path.join(target, ".claude", "projects", slug, "memory")
}

function hookCommands(config) {
  const result = []
  const walk = value => {
    if (Array.isArray(value)) value.forEach(walk)
    else if (value && typeof value === "object") {
      for (const [key, child] of Object.entries(value)) {
        if (key === "command" && typeof child === "string") result.push(child)
        else walk(child)
      }
    }
  }
  walk(config)
  return result
}

test("empty home supports dry-run and the full idempotent lifecycle", () => {
  const target = fs.mkdtempSync(path.join(os.tmpdir(), "ai-working-empty-"))

  const dry = run(target, "--dry-run")
  assert.match(dry, /DRY-RUN 완료/)
  assert.equal(fs.readdirSync(target).length, 0)

  run(target)
  run(target, "--status")
  assert.match(run(target), /변경 0개/)
  assert.equal(fs.readlinkSync(path.join(target, ".codex", "AGENTS.md")), path.join(repo, "global", "CLAUDE.md"))
  assert.equal(fs.lstatSync(memoryPath(target)).isDirectory(), true)

  fs.rmSync(target, { recursive: true, force: true })
})

test("public-only bootstrap migrates legacy managed state and is idempotent", () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "ai-working-bootstrap-"))
  const target = path.join(temp, "target root")
  const legacy = path.join(temp, "ai-working-private")
  const marketplace = path.join(temp, "marketplace", "external-skill")
  fs.mkdirSync(path.join(target, ".claude", "skills"), { recursive: true })
  fs.mkdirSync(path.join(target, ".agents", "skills"), { recursive: true })
  fs.mkdirSync(path.join(target, ".codex"), { recursive: true })
  fs.mkdirSync(path.join(legacy, "skills", "dev-protocol"), { recursive: true })
  fs.mkdirSync(path.join(legacy, "skills", "stale-skill"), { recursive: true })
  fs.mkdirSync(path.join(legacy, "global"), { recursive: true })
  fs.mkdirSync(path.join(legacy, "memory"), { recursive: true })
  fs.mkdirSync(marketplace, { recursive: true })
  fs.writeFileSync(path.join(legacy, "global", "AI-WORKING.md"), "legacy\n")
  fs.writeFileSync(path.join(legacy, "memory", "kept.md"), "preserve me\n")

  fs.symlinkSync(path.join(legacy, "global", "AI-WORKING.md"), path.join(target, ".codex", "AGENTS.md"))
  for (const root of [path.join(target, ".claude", "skills"), path.join(target, ".agents", "skills")]) {
    fs.symlinkSync(path.join(legacy, "skills", "dev-protocol"), path.join(root, "dev-protocol"))
    fs.symlinkSync(path.join(legacy, "skills", "stale-skill"), path.join(root, "stale-skill"))
  }
  fs.symlinkSync(marketplace, path.join(target, ".agents", "skills", "external-skill"))
  fs.mkdirSync(path.dirname(memoryPath(target)), { recursive: true })
  fs.symlinkSync(path.join(legacy, "memory"), memoryPath(target))

  const claudeFile = path.join(target, ".claude", "CLAUDE.md")
  fs.writeFileSync(
    claudeFile,
    [
      "# existing",
      "<!-- BEGIN AGENT-DEV-CONSORTIUM (auto) -->",
      `@${legacy}/global/AI-WORKING.md`,
      "<!-- END AGENT-DEV-CONSORTIUM (auto) -->",
      "",
    ].join("\n"),
  )
  const externalHook = "$HOME/.local/hooks/external.sh"
  const oldManagedHook = "node $HOME/.claude/hooks/preview-db-guard.mjs"
  const settings = {
    theme: "dark",
    hooks: {
      PreToolUse: [
        { matcher: "Bash", hooks: [{ type: "command", command: externalHook }] },
        { matcher: "Bash", hooks: [{ type: "command", command: oldManagedHook, timeout: 99 }] },
      ],
    },
  }
  fs.writeFileSync(path.join(target, ".claude", "settings.json"), JSON.stringify(settings))
  fs.writeFileSync(
    path.join(target, ".codex", "hooks.json"),
    JSON.stringify({ hooks: { PreToolUse: [{ hooks: [{ type: "command", command: oldManagedHook }] }] } }),
  )

  const beforeDevProtocol = fs.readlinkSync(path.join(target, ".claude", "skills", "dev-protocol"))
  const beforeMemory = fs.readlinkSync(memoryPath(target))
  const dry = run(target, "--dry-run")
  assert.match(dry, /DRY-RUN/)
  assert.equal(fs.readlinkSync(path.join(target, ".claude", "skills", "dev-protocol")), beforeDevProtocol)
  assert.equal(fs.readlinkSync(memoryPath(target)), beforeMemory)
  assert.match(fs.readFileSync(claudeFile, "utf8"), /AGENT-DEV-CONSORTIUM/)

  run(target)

  assert.equal(fs.readlinkSync(path.join(target, ".codex", "AGENTS.md")), path.join(repo, "global", "CLAUDE.md"))
  assert.equal(fs.readlinkSync(path.join(target, ".claude", "skills", "dev-protocol")), path.join(repo, "skills", "dev-protocol"))
  assert.equal(fs.readlinkSync(path.join(target, ".agents", "skills", "dev-protocol")), path.join(repo, "skills", "dev-protocol"))
  assert.equal(fs.existsSync(path.join(target, ".claude", "skills", "stale-skill")), false)
  assert.equal(fs.existsSync(path.join(target, ".agents", "skills", "stale-skill")), false)
  assert.equal(fs.readlinkSync(path.join(target, ".agents", "skills", "external-skill")), marketplace)

  const migratedMemory = memoryPath(target)
  assert.equal(fs.lstatSync(migratedMemory).isDirectory(), true)
  assert.equal(fs.lstatSync(migratedMemory).isSymbolicLink(), false)
  assert.equal(fs.readFileSync(path.join(migratedMemory, "kept.md"), "utf8"), "preserve me\n")

  const claudeText = fs.readFileSync(claudeFile, "utf8")
  assert.doesNotMatch(claudeText, /AGENT-DEV-CONSORTIUM/)
  assert.ok(claudeText.includes(path.join(repo, "global", "CLAUDE.md")))

  const installedSettings = JSON.parse(fs.readFileSync(path.join(target, ".claude", "settings.json"), "utf8"))
  assert.equal(installedSettings.theme, "dark")
  assert.ok(hookCommands(installedSettings).includes(externalHook))
  assert.equal(hookCommands(installedSettings).filter(command => command === oldManagedHook).length, 2)
  const codexSettings = JSON.parse(fs.readFileSync(path.join(target, ".codex", "hooks.json"), "utf8"))
  assert.equal(hookCommands(codexSettings).filter(command => command === oldManagedHook).length, 2)

  run(target, "--status")
  const second = run(target)
  assert.match(second, /변경 0개/)

  fs.rmSync(temp, { recursive: true, force: true })
})

test("status is read-only and fails when installation is missing", () => {
  const target = fs.mkdtempSync(path.join(os.tmpdir(), "ai-working-status-"))
  const result = spawnSync("/bin/bash", [script, "--target-root", target, "--status"], {
    cwd: repo,
    encoding: "utf8",
  })
  assert.notEqual(result.status, 0)
  assert.equal(fs.readdirSync(target).length, 0)
  fs.rmSync(target, { recursive: true, force: true })
})
