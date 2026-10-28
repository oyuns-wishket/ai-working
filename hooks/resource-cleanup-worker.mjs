#!/usr/bin/env node
// Detached, serialized execution. Never discard ownership on failed shutdown.
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'

let raw = ''
for await (const chunk of process.stdin) raw += chunk
const plan = JSON.parse(raw)
const results = []
function command(bin, args, cwd) {
  try { return { ok: true, output: execFileSync(bin, args, { cwd, timeout: 60000, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim() } }
  catch { return { ok: false, output: '' } }
}
function record(resource, status) { results.push({ resource, status }) }
function stopped(id) {
  const result = command('docker', ['inspect', '--format', '{{.State.Running}}', id])
  return result.ok && result.output === 'false'
}
for (const id of plan.containers) {
  const all = command('docker', ['ps', '-aq', '--no-trunc'])
  if (all.ok && !all.output.split('\n').includes(id)) { record(id, 'already-absent'); continue }
  const result = command('docker', ['stop', '-t', '3', id])
  record(id, result.ok && stopped(id) ? 'stopped' : 'failed')
}
for (const id of plan.disposable) {
  // Recheck explicit opt-in immediately before removal. Never use -v or -f.
  const label = command('docker', ['inspect', '--format', '{{index .Config.Labels "ai-working.disposable"}}', id])
  if (results.some(r => r.resource === id && r.status === 'already-absent')) continue
  if (!label.ok) { record(id, 'failed'); continue }
  if (label.output !== 'true') { record(id, 'retained'); continue }
  if (!stopped(id)) { record(id, 'failed'); continue }
  const removed = command('docker', ['rm', id])
  // Engine-wide ID listing distinguishes absence from an inspect/daemon error.
  const remaining = command('docker', ['ps', '-aq', '--no-trunc'])
  record(id, removed.ok && remaining.ok && !remaining.output.split('\n').includes(id) ? 'removed' : 'failed')
}
if (plan.unresolvedSupabase) record('supabase', 'failed')
if (plan.supabase) {
  const s = plan.supabase
  const cwd = fs.existsSync(s.root) ? s.root : os.tmpdir()
  const scope = command('docker', ['ps', '-q', '--no-trunc', '--filter', `label=com.supabase.cli.project=${s.projectId}`])
  const exact = scope.ok && JSON.stringify(scope.output.split('\n').filter(Boolean).sort()) === JSON.stringify([...s.ids].sort())
  const result = exact ? command('supabase', ['stop', '--project-id', s.projectId], cwd) : { ok: false }
  const running = command('docker', ['ps', '-q', '--no-trunc'])
  record('supabase', result.ok && running.ok && !s.ids.some(id => running.output.split('\n').includes(id)) ? 'stopped' : 'failed')
}
if (plan.quitApp && !results.some(r => r.status === 'failed')) {
  const remaining = command('docker', ['ps', '-q'])
  if (remaining.ok && !remaining.output) {
    const result = command('docker', ['desktop', 'stop', '--detach', '--force'])
    record('docker-desktop', result.ok ? 'stop-requested' : 'failed')
  } else record('docker-desktop', remaining.ok ? 'kept-busy' : 'failed')
}
const receipt = path.join(plan.cache, 'cleanup-results', `${plan.sessionId}.json`)
fs.mkdirSync(path.dirname(receipt), { recursive: true, mode: 0o700 })
fs.writeFileSync(receipt, JSON.stringify({ at: new Date().toISOString(), results }) + '\n', { mode: 0o600 })
if (!results.some(r => r.status === 'failed')) {
  try {
    const contents = fs.readFileSync(plan.file)
    // A resumed session may have registered new resources while we ran.
    if (createHash('sha256').update(contents).digest('hex') === plan.fingerprint) fs.unlinkSync(plan.file)
  } catch { /* Already consumed; receipt remains. */ }
}
