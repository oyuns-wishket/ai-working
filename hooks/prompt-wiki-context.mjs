#!/usr/bin/env node
// UserPromptSubmit: route a substantive prompt through the project's connected wiki and inject
// the matching document titles and paths (never bodies). 2026-10-22: a session-start notice
// alone led to 1 wiki route in 25 substantial sessions of the largest connected project;
// putting the relevant paths next to the prompt removes the "remember to route" step.
// Read-only, fail-open, bounded; silent outside wiki-connected projects.
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const MIN_PROMPT_CHARS = 12;      // "ㅇㅋ", "다음", "커밋해" carry no retrievable intent
const MAX_DOCS = 4;
const MAX_CONTEXT_BYTES = 3200;
const SUMMARY_CHARS = 160;
// 2026-10-25: generic prompts ("커밋하고 PR 올려줘") matched every note at 30; real topics scored 60+.
const MIN_SCORE = 40;
const ISSUE_TIMEOUT_MS = 2500;
const ROUTE_TIMEOUT_MS = 4000;

let raw = '';
for await (const chunk of process.stdin) {
  raw += chunk;
  if (Buffer.byteLength(raw) > 256 * 1024) process.exit(0);
}
let input;
try { input = JSON.parse(raw || '{}'); } catch { process.exit(0); }
if (process.env.AI_WORKING_PROMPT_WIKI === '0') process.exit(0);
const prompt = String(input.prompt || '').trim();
if (prompt.length < MIN_PROMPT_CHARS || prompt.startsWith('/')) process.exit(0);
// 2026-10-31: UserPromptSubmit also fires for system-generated turns — background task
// notifications, cross-session messages, interruption notices. Routing those produced 26
// injections for 7 real prompts in one session, mostly unrelated notes. Only a human prompt routes.
if (/^(<task-notification>|<cross-session-message|<system-reminder>|<command-|\[Request interrupted|Caveat:)/.test(prompt)) process.exit(0);
const cwd = input.cwd || process.cwd();
const resolver = path.join(os.homedir(), '.claude', 'skills', 'project-wiki-context', 'scripts', 'wiki_context.py');
if (!fs.existsSync(resolver)) process.exit(0);

// Strip pasted logs/code so the query stays the user's intent, then bound it. A lane prompt
// (multi-session-dev) is mostly boilerplate; its `## Task` and acceptance sections carry the intent.
function intent(text) {
  const sections = [...text.matchAll(/^## (Task|Acceptance criteria|Goal)[^\n]*\n([\s\S]*?)(?=^## |$(?![\s\S]))/gm)].map((m) => m[2]);
  return sections.length ? sections.join(' ') : text;
}
// Lane prompts are written in English while the wiki is Korean: an English-only query matched
// nothing above noise. Issue numbers name the work, so their (Korean) titles join the query.
function issueTitles(text, dir) {
  const numbers = [...new Set([...text.matchAll(/(?<![\w/])#(\d{2,6})\b/g)].map((m) => m[1]))].slice(0, 3);
  const titles = [];
  for (const number of numbers) {
    const r = spawnSync('gh', ['issue', 'view', number, '--json', 'title', '-q', '.title'],
      { cwd: dir, encoding: 'utf8', timeout: ISSUE_TIMEOUT_MS });
    if (r.status === 0 && r.stdout.trim()) titles.push(r.stdout.trim().slice(0, 120));
  }
  return titles;
}
const focus = intent(prompt).replace(/```[\s\S]*?```/g, ' ');
const hangul = (focus.match(/[가-힣]/g) || []).length;
const extra = hangul < 20 && fs.existsSync(cwd) ? issueTitles(focus, cwd) : [];
const query = [...extra, focus].join(' ').replace(/\s+/g, ' ').slice(0, 400);
const result = spawnSync('python3', [resolver, 'route', '--project', cwd, '--query', query,
  '--record', '--sample-kind', 'development'], { encoding: 'utf8', timeout: ROUTE_TIMEOUT_MS, maxBuffer: 2 * 1024 * 1024 });
let routed;
try { routed = JSON.parse(result.stdout); } catch { process.exit(0); }
if (!routed || routed.mode !== 'wiki-bounded') process.exit(0);
const docs = (routed.documents || []).filter((d) => d && d.relative_path && (d.score ?? MIN_SCORE) >= MIN_SCORE).slice(0, MAX_DOCS);
if (!docs.length) process.exit(0);

// Same document already offered in this session → do not repeat it.
const session = String(input.session_id || 'unknown').replace(/[^a-zA-Z0-9_.-]/g, '_');
const stateDir = path.join(os.homedir(), '.local', 'state', 'ai-working', 'prompt-wiki');
const stateFile = path.join(stateDir, `${session}.json`);
let seen = [];
try { seen = JSON.parse(fs.readFileSync(stateFile, 'utf8')); } catch { /* first prompt */ }
const fresh = docs.filter((d) => !seen.includes(d.relative_path));
if (!fresh.length) process.exit(0);
try {
  fs.mkdirSync(stateDir, { recursive: true, mode: 0o700 });
  fs.writeFileSync(stateFile, JSON.stringify([...seen, ...fresh.map((d) => d.relative_path)].slice(-200)));
} catch { /* dedup is best-effort */ }

// 2026-10-25: 70 offered paths across 14 sessions were opened 0 times. A bare path list is easy to
// skip, so each line now carries the note's own summary (the agent can judge relevance without
// opening it) and the instruction names the step: read the matching one before deciding.
function summary(file) {
  try {
    const head = fs.readFileSync(file, 'utf8').slice(0, 20000);
    const body = head.replace(/^---\n[\s\S]*?\n---\n/, '');
    const quoted = body.match(/^> (.+)$/m);
    const section = body.match(/^## 요약\s*\n+([^\n#][^\n]*)/m);
    const line = (quoted?.[1] || section?.[1] || '').replace(/\s+/g, ' ').trim();
    return line.length > SUMMARY_CHARS ? `${line.slice(0, SUMMARY_CHARS - 1)}…` : line;
  } catch { return ''; }
}
const root = routed.wiki_root || '';
const lines = fresh.map((d) => {
  const where = d.read_mode === 'sections' && Array.isArray(d.sections) && d.sections.length
    ? ` (lines ${d.sections.map((s) => `${s.line_start}-${s.line_end}`).join(', ')})` : '';
  const kind = d.corpus === 'manual' ? '내 메모' : (d.type || 'note');
  const file = path.join(root, d.relative_path);
  const gist = summary(file);
  return `- ${d.title} [${kind}]${gist ? ` — ${gist}` : ''}\n  ${file}${where}`;
});
const trace = routed.retrieval_feedback?.trace_id;
let text = `[wiki 관련 문서] 이 프로젝트 wiki에서 요청과 맞는 문서입니다. 요약을 보고 관련 있는 문서는 설계·구현 결정 전에 Read로 읽으세요(sections 범위만). 사용자에게 되묻기 전에 아래 요약에 답이 있는지 먼저 확인합니다. 관련 없으면 무시하고, 현재 코드·migration·운영 증거와 다르면 코드를 따릅니다.\n${lines.join('\n')}`;
if (trace) text += `\n(trace ${trace} — 완료 보고 때 실제로 쓴 문서는 used, 안 쓴 건 not_used로 retrieval_feedback.py feedback 마감)`;
if (Buffer.byteLength(text) > MAX_CONTEXT_BYTES) text = Buffer.from(text).subarray(0, MAX_CONTEXT_BYTES).toString('utf8').replace(/\uFFFD$/, '');
console.log(JSON.stringify({ hookSpecificOutput: { hookEventName: 'UserPromptSubmit', additionalContext: text } }));
