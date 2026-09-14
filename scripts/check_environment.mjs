#!/usr/bin/env node
// Read-only behavior diagnostics. Installation parity remains bootstrap --status.
import fs from "node:fs"
import path from "node:path"
import { readWorkspaceConfig, matchWorkspace } from "../hooks/workspace-config.mjs"

try {
  const projects = []
  for (let index = 2; index < process.argv.length; index++) {
    const arg = process.argv[index]
    if (arg === "--project" && process.argv[index + 1]) projects.push(path.resolve(process.argv[++index]))
    else if (arg !== "--json") throw new Error("usage: check_environment.mjs [--project <path>]... [--json]")
  }
  const config = readWorkspaceConfig()
  const roots = config.workspace_roots.map(root => ({ path: root, exists: fs.existsSync(root) }))
  const results = projects.map(project => {
    const handoff = path.join(project, "docs", "handoff", "HANDOFF.md")
    const bytes = fs.existsSync(handoff) ? fs.statSync(handoff).size : null
    return {
      project,
      exists: fs.existsSync(project),
      matched_workspace: matchWorkspace(project, config),
      handoff_source_bytes: bytes,
      handoff_exceeds_context_budget: bytes !== null && bytes > 8192,
    }
  })
  const report = {
    status: roots.some(root => !root.exists) || results.some(project => !project.exists) ? "attention" : "ok",
    configuration: config,
    roots,
    projects: results,
    notes: [
      "Workspace matching covers advisory branch/implementation-note hooks; it does not install project rules or register a wiki.",
      "A large handoff is preserved on disk; session-start emits a bounded current-section excerpt.",
      "Run bootstrap.sh --status for installation parity and node --test tests/*.test.mjs for behavior regression checks.",
    ],
  }
  console.log(JSON.stringify(report, null, 2))
  if (report.status !== "ok") process.exitCode = 1
} catch (error) {
  console.log(JSON.stringify({ status: "error", error: error.message }))
  process.exitCode = 2
}
