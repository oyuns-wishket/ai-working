// Read-only check: does this fresh Paseo workspace still need a short Korean title?
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

export const MAX_TITLE_CHARS = 10;
const FRESH_WORKSPACE_MS = 10 * 60 * 1000;
const NOTICE = `[Paseo 제목] 이 워크스페이스에는 한국어 제목 지시문이 없다. 첫 요청을 파악한 직후 Paseo MCP의 rename_workspace를 workspaceId 없이 한 번 호출해, 한국어 ${MAX_TITLE_CHARS}자 이내(공백 포함) 명사형 작업 이름으로 제목을 바꾼다. 예: "현금영수증 취소", "로그인 복구". Paseo MCP가 없으면 건너뛴다.`;

const readJson = file => { try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return null; } };

export const isShortKoreanTitle = title =>
  typeof title === 'string' && /[가-힣]/.test(title) && [...title.trim()].length <= MAX_TITLE_CHARS;

function findAgent(paseoHome, agentId) {
  const root = path.join(paseoHome, 'agents');
  let dirs = [];
  try { dirs = fs.readdirSync(root); } catch { return null; }
  for (const dir of dirs) {
    const agent = readJson(path.join(root, dir, `${agentId}.json`));
    if (agent) return agent;
  }
  return null;
}

const hasTitleInstructions = root => {
  const text = root && readJson(path.join(root, 'paseo.json'))?.metadataGeneration?.title?.instructions;
  return typeof text === 'string' && text.trim() !== '';
};

export function paseoTitleNotice(env = process.env, now = Date.now()) {
  const agentId = env.PASEO_AGENT_ID;
  if (!agentId || !/^[\w-]+$/.test(agentId)) return '';
  const paseoHome = env.PASEO_HOME || path.join(os.homedir(), '.paseo');
  const agent = findAgent(paseoHome, agentId);
  if (!agent?.workspaceId || agent.internal) return '';
  const workspaces = readJson(path.join(paseoHome, 'projects', 'workspaces.json'));
  const workspace = Array.isArray(workspaces) && workspaces.find(item => item?.workspaceId === agent.workspaceId);
  if (!workspace) return '';
  // Older workspaces keep whatever title the user or an earlier session chose.
  const age = now - Date.parse(workspace.createdAt);
  if (!(age >= 0 && age <= FRESH_WORKSPACE_MS)) return '';
  // Paseo generates the title itself when the repository carries the instructions.
  const roots = workspace.isPaseoOwnedWorktree ? [workspace.mainRepoRoot] : [workspace.worktreeRoot, workspace.cwd];
  if (roots.some(hasTitleInstructions)) return '';
  // A first-prompt placeholder equals the agent title; Paseo may still replace it with an English one.
  if (isShortKoreanTitle(workspace.title) && workspace.title !== agent.title) return '';
  return NOTICE;
}
