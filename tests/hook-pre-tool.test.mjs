import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import test from "node:test"
import { execFileSync } from "node:child_process"

test("migration hook permits review and explicit confirmed execution while rejecting unconfirmed writes", t => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), "pre-tool-policy-"))
  t.after(() => fs.rmSync(home, { recursive: true, force: true }))
  fs.mkdirSync(path.join(home, ".claude", "hooks"), { recursive: true })
  fs.copyFileSync("hooks/lib.sh", path.join(home, ".claude", "hooks", "lib.sh"))
  const invoke = command => execFileSync("/bin/sh", ["hooks/pre-tool.sh"], {
    encoding: "utf8", env: { ...process.env, HOME: home },
    // These are input strings for the hook; no migration command is executed.
    input: JSON.stringify({ tool_name: "Bash", tool_input: { command } }),
  }).trim()
  assert.equal(invoke("supabase db push --dry-run"), "")
  assert.equal(invoke("CONFIRMED=1 supabase db push"), "")
  assert.equal(invoke("git status --short"), "")
  const denied = JSON.parse(invoke("supabase db push")).hookSpecificOutput
  assert.equal(denied.permissionDecision, "deny")
  assert.equal(JSON.parse(invoke("echo CONFIRMED=1; supabase db push")).hookSpecificOutput.permissionDecision, "deny")
})

test("quoted destructive SQL is blocked but documentation is allowed", () => {
  const invoke = command => execFileSync('/bin/bash', ['hooks/block-dangerous.sh'], {
    encoding: 'utf8', input: JSON.stringify({ tool_name: 'Bash', tool_input: { command } }),
  }).trim();
  for (const command of ["psql -c 'DROP TABLE example_table'", 'mysql -e "DROP DATABASE sample"', 'git status; psql -c "DROP SCHEMA demo"', 'echo preparing\npsql -c "DROP TABLE example_table"']) {
    assert.equal(JSON.parse(invoke(command)).hookSpecificOutput.permissionDecision, 'deny');
  }
  for (const command of ["echo \"psql -c 'DROP TABLE example_table'\"", "psql -c 'SELECT 1'", `psql -c "SELECT 'DROP TABLE example_table';"`, 'git status --short']) assert.equal(invoke(command), '');
});

test("retired handoff hook never modifies or pushes a repository", t => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'handoff-retired-'));
  t.after(() => fs.rmSync(home, { recursive: true, force: true }));
  fs.mkdirSync(path.join(home, 'docs/handoff'), { recursive: true });
  fs.writeFileSync(path.join(home, 'docs/handoff/HANDOFF.md'), 'unchanged\n');
  execFileSync('git', ['init', '-q'], { cwd: home });
  const payload = path.join(home, 'hook-input.json');
  fs.writeFileSync(payload, JSON.stringify({ cwd: home }));
  const before = execFileSync('git', ['status', '--porcelain'], { cwd: home, encoding: 'utf8' });
  // The no-op may exit before Node writes a pipe. Keep stdin available without
  // a parent writer racing the child exit (EPIPE on Linux).
  const input = fs.openSync(payload, 'r');
  try {
    execFileSync('/bin/sh', [path.resolve('hooks/handoff-sync.sh')], { cwd: home, stdio: [input, 'pipe', 'pipe'] });
  } finally {
    fs.closeSync(input);
  }
  assert.equal(fs.readFileSync(path.join(home, 'docs/handoff/HANDOFF.md'), 'utf8'), 'unchanged\n');
  assert.equal(execFileSync('git', ['status', '--porcelain'], { cwd: home, encoding: 'utf8' }), before);
});
