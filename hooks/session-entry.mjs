#!/usr/bin/env node
// One bounded, read-only startup context for both native hook runtimes.
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

let raw = '';
for await (const chunk of process.stdin) {
  raw += chunk;
  if (Buffer.byteLength(raw) > 1024 * 1024) process.exit(0);
}
let input;
try { input = JSON.parse(raw || '{}'); } catch { process.exit(0); }
const dir = path.dirname(fileURLToPath(import.meta.url));
const parts = [];
for (const name of ['session-context.sh', 'session-start.sh']) {
  const result = spawnSync('/bin/bash', [path.join(dir, name)], {
    cwd: input.cwd || process.cwd(), input: raw, encoding: 'utf8',
    timeout: name === 'session-context.sh' ? 2000 : 9000, maxBuffer: 32 * 1024,
  });
  try {
    const context = JSON.parse(result.stdout).hookSpecificOutput?.additionalContext;
    if (context) parts.push(name === 'session-context.sh' ? context.slice(0, 512) : context);
  } catch { /* Missing optional context must not block a session. */ }
}
// Reserve the existing 8 KiB handoff budget; basic metadata is capped separately.
const text = parts.join('\n');
if (text) console.log(JSON.stringify({ hookSpecificOutput: {
  hookEventName: 'SessionStart', additionalContext: text,
}}));
