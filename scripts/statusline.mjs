#!/usr/bin/env node
// Native Claude JSON input only: no network, credentials, subprocesses or caches.
import path from 'node:path';

let raw = '';
for await (const chunk of process.stdin) {
  raw += chunk;
  if (Buffer.byteLength(raw) > 64 * 1024) process.exit(0);
}
try {
  const input = JSON.parse(raw || '{}');
  const clean = value => String(value || '').replace(/[\x00-\x1f\x7f-\x9f]/g, '').slice(0, 80);
  const parts = [];
  const model = clean(input.model?.display_name || input.model?.id);
  const project = clean(path.basename(input.workspace?.current_dir || input.cwd || ''));
  if (model) parts.push(model);
  if (project) parts.push(project);
  const used = input.context_window?.used_percentage;
  if (typeof used === 'number' && Number.isFinite(used) && used >= 0 && used <= 100) {
    parts.push(`context ${Math.round(used)}% used`);
  }
  if (parts.length) process.stdout.write(parts.join(' | ') + '\n');
} catch { /* Missing/invalid optional status information stays quiet. */ }
