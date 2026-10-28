import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import test from 'node:test'

const worker = path.resolve('hooks/resource-cleanup-worker.mjs')
test('disposable cleanup preserves volumes, retains failures and verifies outcomes', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'cleanup-worker-'))
  const bin = path.join(root, 'bin')
  fs.mkdirSync(bin)
  const state = path.join(root, 'state.json')
  const id = 'a'.repeat(64)
  const other = 'b'.repeat(64)
  const docker = path.join(bin, 'docker')
  fs.writeFileSync(docker, `#!${process.execPath}
const fs = require('fs'); const a = process.argv.slice(2); const p = process.env.STATE;
const s = JSON.parse(fs.readFileSync(p)); s.calls.push(a);
if (a[0] === 'stop') { if (s.fail) process.exit(1); s.running = false }
if (a[0] === 'rm') { if (s.fail) process.exit(1); s.exists = false }
if (a[0] === 'ps') process.stdout.write((s.exists ? '${id}\\n' : '') + '${other}');
if (a[0] === 'inspect') process.stdout.write(a[2].includes('disposable') ? String(s.label) : String(s.running));
fs.writeFileSync(p, JSON.stringify(s));
`)
  fs.chmodSync(docker, 0o755)
  const file = path.join(root, 'session.json')
  const run = (disposable, fail, label = true) => {
    fs.writeFileSync(file, '{"ownershipVersion":2}')
    fs.writeFileSync(state, JSON.stringify({ exists: true, running: true, label, fail, calls: [] }))
    const plan = { containers: [id], disposable: disposable ? [id] : [], cache: root, file, sessionId: 'test', fingerprint: createHash('sha256').update(fs.readFileSync(file)).digest('hex') }
    execFileSync(process.execPath, [worker], { input: JSON.stringify(plan), env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, STATE: state } })
    return { state: JSON.parse(fs.readFileSync(state)), result: JSON.parse(fs.readFileSync(path.join(root, 'cleanup-results/test.json'))) }
  }
  try {
    let r = run(true, false)
    assert.equal(r.state.exists, false)
    assert.equal(fs.existsSync(file), false)
    assert.equal(r.result.results.at(-1).status, 'removed')
    assert.ok(r.state.calls.every(a => !a.includes('-v') && !a.includes('-f') && !a.includes(other)))
    r = run(false, false)
    assert.equal(r.state.exists, true, 'unmarked container data preserved')
    r = run(true, true)
    assert.equal(fs.existsSync(file), true, 'failure preserves retry evidence')
    assert.ok(r.result.results.some(r => r.status === 'failed'))
    r = run(true, false, false)
    assert.equal(r.state.exists, true, 'changed label refuses removal')
    assert.equal(fs.existsSync(file), false)
    fs.writeFileSync(file, '{}')
    execFileSync(process.execPath, [worker], { input: JSON.stringify({ containers: [], disposable: [], supabase: { root, projectId: 'old-stack', ids: [id] }, cache: root, file, sessionId: 'changed-stack', fingerprint: createHash('sha256').update('{}').digest('hex') }), env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, STATE: state } })
    assert.equal(fs.existsSync(file), true, 'changed Supabase identity retains evidence')
    assert.equal(JSON.parse(fs.readFileSync(path.join(root, 'cleanup-results/changed-stack.json'))).results[0].status, 'failed')
  } finally { fs.rmSync(root, { recursive: true, force: true }) }
})
