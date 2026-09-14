import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import test from 'node:test';

const run = input => execFileSync('node', ['scripts/statusline.mjs'], { input, encoding: 'utf8' });
test('status display uses supplied native fields without inventing metrics', () => {
  assert.equal(run(JSON.stringify({ model: { display_name: 'Model' }, workspace: { current_dir: '/example/project' }, context_window: { used_percentage: 32.6 } })), 'Model | project | context 33% used\n');
  assert.equal(run(JSON.stringify({ model: { id: 'model-id' }, context_window: { used_percentage: null } })), 'model-id\n');
});
test('invalid, oversized and terminal-control inputs stay bounded', () => {
  assert.equal(run('{invalid'), '');
  assert.equal(run('{}'), '');
  assert.equal(run('x'.repeat(70000)), '');
  assert.equal(run(JSON.stringify({ model: { id: 'model\n\u001b[31m' } })), 'model[31m\n');
});
