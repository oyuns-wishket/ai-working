#!/usr/bin/env node
// PreToolUse (Flowpass MCP tools): hold the first input call of each user request once and return
// the input rules as the denial reason, so the agent rewrites its content before anything reaches
// the server. Context attached to this event is shown next to the tool result, after the save.
// Lookups pass untouched. A missing rules file or unwritable state never blocks Flowpass.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Every tool not listed here counts as input, so a write tool the plugin adds later is covered.
const LOOKUP_TOOLS = new Set(['flowpass_start', 'flowpass_status', 'flowpass_read', 'flowpass_discover',
  'flowpass_guide', 'flowpass_board', 'flowpass_options', 'flowpass_context', 'flowpass_begin_run',
  'flowpass_feedback_list']);
// Calls issued in the same assistant message were composed before the rules were seen.
// 2026-11-21: parallel calls reached the hook 0.1 s apart and a retry 2.0 s or more after the
// hold. A 4 s window held every retry a second time.
const SAME_MESSAGE_MS = 1500;
// A request that runs longer than this, or a runtime that reports no request id, gets the rules again.
const REPEAT_AFTER_MS = 10 * 60 * 1000;
const TAG = '[Flowpass 입력 규칙]';

const deny = reason => ({ hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny', permissionDecisionReason: reason } });
const warn = message => ({ systemMessage: `${TAG} ${message}` });

function readRules() {
  const here = path.dirname(fileURLToPath(import.meta.url));
  // Installed: linked next to the hook by manifest.json. Repository checkout: global/.
  for (const file of [path.join(here, 'flowpass-input-rules.md'), path.join(here, '..', 'global', 'flowpass-input-rules.md')]) {
    try {
      const text = fs.readFileSync(file, 'utf8').trim();
      if (text) return { text, file };
    } catch { /* try the next location */ }
  }
  return null;
}

function decide(input) {
  const tool = String(input.tool_name || '');
  // Claude: mcp__plugin_flowpass_flowpass__flowpass_write. Codex: mcp__flowpass__flowpass_write.
  if (!/^mcp__.*flowpass/i.test(tool) || LOOKUP_TOOLS.has(tool.split('__').pop())) return null;
  const rules = readRules();
  if (!rules) return warn('규칙 파일을 읽지 못해 규칙 전달 없이 진행했다. ai-working에서 ./bootstrap.sh를 다시 실행한다.');

  const session = String(input.session_id || 'unknown').replace(/[^a-zA-Z0-9_.-]/g, '_');
  const stateDir = path.join(os.homedir(), '.local', 'state', 'ai-working', 'flowpass-input-rules');
  const stateFile = path.join(stateDir, `${session}.json`);
  let state = {};
  try { state = JSON.parse(fs.readFileSync(stateFile, 'utf8')) || {}; } catch { /* first input call of the session */ }
  // A subagent has its own context, so it gets its own delivery.
  const reader = String(input.agent_id || 'main');
  const request = input.prompt_id ? `prompt:${input.prompt_id}` : input.turn_id ? `turn:${input.turn_id}` : 'unknown';
  const now = Date.now();
  const last = state[reader];
  const elapsed = last && last.request === request ? now - last.at : Infinity;
  if (elapsed >= SAME_MESSAGE_MS && elapsed < REPEAT_AFTER_MS) return null;
  if (elapsed >= 0 && elapsed < SAME_MESSAGE_MS) {
    return deny(`${TAG} 방금 전달한 규칙을 보기 전에 작성된 호출이라 함께 보류했다. 내용을 규칙에 맞게 고친 뒤 다시 호출한다.`);
  }
  try {
    fs.mkdirSync(stateDir, { recursive: true, mode: 0o700 });
    fs.writeFileSync(stateFile, JSON.stringify({ ...state, [reader]: { request, at: now } }));
  } catch {
    // Without a record every retry would be held again and Flowpass input would stop.
    return warn('전달 기록을 저장하지 못해 규칙 전달 없이 진행했다.');
  }
  return deny(`${TAG} 이 호출은 저장 전에 규칙을 전달하려고 한 번 보류했다. 에이전트가 작성하는 문장을 아래 규칙에 맞게 고친 뒤 같은 도구를 다시 호출하면 실행된다. 사용자가 직접 말한 값과 원문 인용(제목·이름·딜명·사유·근거 quote)은 바꾸지 않는다.\n\n${rules.text}\n\n(원본: ${rules.file})`);
}

let raw = '';
for await (const chunk of process.stdin) raw += chunk;
let input = null;
try { input = JSON.parse(raw || '{}'); } catch { /* unreadable input: let the call through */ }
const output = input && typeof input === 'object' ? decide(input) : null;
// No process.exit() after writing: a piped stdout can be cut short by it.
if (output) process.stdout.write(`${JSON.stringify(output)}\n`);
