#!/usr/bin/env node
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import { execFileSync } from "node:child_process"
import { pathToFileURL } from "node:url"

function canonical(value, home) {
  if (typeof value !== "string" || !value.trim() || /[\r\n\0]/.test(value)) {
    throw new Error("workspace paths must be nonempty single-line strings")
  }
  const expanded = value === "~" ? home : value.startsWith("~/") ? path.join(home, value.slice(2)) : value
  if (!path.isAbsolute(expanded)) throw new Error("workspace paths must be absolute or start with ~/")
  const resolved = path.resolve(expanded)
  try { return fs.realpathSync(resolved) } catch {
    // Canonicalize the existing ancestor for files that have not been created yet.
    const parent = path.dirname(resolved)
    return parent === resolved ? resolved : path.join(canonical(parent, home), path.basename(resolved))
  }
}

export function readWorkspaceConfig(env = process.env) {
  const home = env.HOME || os.homedir()
  const file = env.AI_WORKING_WORKSPACES_CONFIG || path.join(env.XDG_CONFIG_HOME || path.join(home, ".config"), "ai-working", "workspaces.json")
  let config, source
  if (env.AI_WORKING_PROJECTS_ROOT) {
    config = { workspace_roots: [env.AI_WORKING_PROJECTS_ROOT] }
    source = "AI_WORKING_PROJECTS_ROOT"
  } else if (fs.existsSync(file)) {
    if (fs.statSync(file).size > 65536) throw new Error("workspace config exceeds 64 KiB")
    config = JSON.parse(fs.readFileSync(file, "utf8"))
    source = file
    if (!config || config.schema_version !== 1) throw new Error("workspace config requires schema_version: 1")
  } else {
    config = { workspace_roots: [path.join(home, "aidp")] }
    source = "legacy-default"
  }
  const roots = config.workspace_roots
  const excludes = config.excluded_roots ?? []
  if (!Array.isArray(roots) || !Array.isArray(excludes)) throw new Error("workspace_roots and excluded_roots must be arrays")
  if (roots.length + excludes.length > 128) throw new Error("too many workspace paths")
  return {
    source,
    workspace_roots: [...new Set(roots.map(value => canonical(value, home)))],
    excluded_roots: [...new Set(excludes.map(value => canonical(value, home)))],
  }
}

function inside(candidate, root) {
  const relative = path.relative(root, candidate)
  return relative === "" || (relative !== ".." && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative))
}

export function matchWorkspace(candidate, config, env = process.env) {
  const resolved = canonical(candidate, env.HOME || os.homedir())
  const match = target => {
    if (config.excluded_roots.some(root => inside(target, root))) return null
    return [...config.workspace_roots].sort((a, b) => b.length - a.length).find(root => inside(target, root)) || null
  }
  if (config.excluded_roots.some(root => inside(resolved, root))) return null
  const direct = match(resolved)
  // Check repository ownership even for a directly matched worktree, so excluded
  // repositories cannot re-enter through a worktree under another managed root.
  let directory = resolved
  try { if (!fs.statSync(directory).isDirectory()) directory = path.dirname(directory) } catch { directory = path.dirname(directory) }
  try {
    const common = execFileSync("git", ["-C", directory, "rev-parse", "--git-common-dir"], {
      encoding: "utf8", timeout: 1000, stdio: ["ignore", "pipe", "ignore"], env,
    }).trim()
    const commonPath = canonical(path.resolve(directory, common), env.HOME || os.homedir())
    if (path.basename(commonPath) === ".git") {
      const owner = path.dirname(commonPath)
      if (config.excluded_roots.some(root => inside(owner, root))) return null
      return direct || match(owner)
    }
  } catch { /* An ordinary file outside Git can still match its workspace. */ }
  return direct
}

if (process.argv[1] && import.meta.url === pathToFileURL(fs.realpathSync(process.argv[1])).href) {
  try {
    const config = readWorkspaceConfig()
    if (process.argv[2] === "match" && process.argv.length === 4) {
      const root = matchWorkspace(process.argv[3], config)
      if (root) console.log(root)
      else process.exitCode = 1
    } else if (process.argv[2] === "show" && process.argv.length === 3) {
      console.log(JSON.stringify(config, null, 2))
    } else {
      throw new Error("usage: workspace-config.mjs show | match <absolute-path>")
    }
  } catch (error) {
    console.error(`[ai-working workspace config] ${error.message}`)
    process.exitCode = 2
  }
}
