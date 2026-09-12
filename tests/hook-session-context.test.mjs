import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import test from "node:test"
import { execFileSync } from "node:child_process"

const repo = path.resolve(".")
const hook = path.join(repo, "hooks", "session-context.sh")

test("session context discovers an arbitrarily located ai-working checkout", () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "ai-working-root-discovery-"))
  const home = path.join(temp, "home")
  const source = path.join(temp, "내 AI 작업실")
  const project = path.join(temp, "project")
  fs.mkdirSync(path.join(home, ".codex"), { recursive: true })
  fs.mkdirSync(path.join(source, "global"), { recursive: true })
  fs.mkdirSync(path.join(source, "skills", "project-wiki-context", "scripts"), { recursive: true })
  fs.mkdirSync(project)
  fs.writeFileSync(path.join(source, "bootstrap.sh"), "#!/bin/bash\n")
  fs.writeFileSync(path.join(source, "global", "CLAUDE.md"), "# policy\n")
  fs.writeFileSync(
    path.join(source, "skills", "project-wiki-context", "scripts", "wiki_context.py"),
    'print("portable-root-resolved")\n',
  )
  const policyLink = path.join(home, ".codex", "AGENTS.md")
  fs.symlinkSync(path.relative(path.dirname(policyLink), path.join(source, "global", "CLAUDE.md")), policyLink)
  execFileSync("git", ["init", "-q"], { cwd: project })

  const env = { ...process.env, HOME: home }
  delete env.AI_WORKING_ROOT
  const output = execFileSync("/bin/bash", [hook], { cwd: project, env, encoding: "utf8" })
  const context = JSON.parse(output).hookSpecificOutput.additionalContext
  assert.match(context, /portable-root-resolved/)
  assert.equal(fs.existsSync(path.join(home, "dev-oh")), false)

  fs.rmSync(temp, { recursive: true, force: true })
})
