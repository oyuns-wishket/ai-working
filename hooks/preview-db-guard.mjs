#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";

const POLICY_RELATIVE_PATH = path.join(".agent", "preview-db-policy.json");
const REMOTE_CACHE_TTL_MS = 30_000;
const READY_STATUSES = new Set([
  "ACTIVE_HEALTHY",
  "FUNCTIONS_DEPLOYED",
  "MIGRATIONS_APPLIED",
  "READY",
]);

function readStdin() {
  return new Promise((resolve) => {
    let raw = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (raw += chunk));
    process.stdin.on("end", () => {
      try {
        resolve(JSON.parse(raw || "{}"));
      } catch {
        resolve({});
      }
    });
  });
}

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch {
    return null;
  }
}

function writeJson(file, value) {
  try {
    fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
    fs.writeFileSync(file, `${JSON.stringify(value)}\n`, { mode: 0o600 });
  } catch {
    // Hook state is an optimization. Enforcement still uses live local state.
  }
}

function isInside(candidate, root) {
  const relative = path.relative(root, candidate);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

function findPolicyUp(start) {
  let current = path.resolve(start);
  while (true) {
    const policyFile = path.join(current, POLICY_RELATIVE_PATH);
    if (fs.existsSync(policyFile)) return { root: current, policyFile };
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
}

function policyMatchesPrompt(policy, prompt) {
  const normalized = prompt.toLocaleLowerCase("en-US");
  return [policy.project, ...(policy.aliases || [])]
    .filter(Boolean)
    .some((alias) => normalized.includes(String(alias).toLocaleLowerCase("en-US")));
}

function discoverPolicy(cwd, prompt, sessionFile) {
  const override = process.env.AGENT_GUARD_POLICY_ROOT;
  if (override) {
    const match = findPolicyUp(override);
    if (match) return match;
  }

  const direct = findPolicyUp(cwd);
  if (direct) return direct;

  const previous = readJson(sessionFile);
  if (previous?.root && fs.existsSync(path.join(previous.root, POLICY_RELATIVE_PATH))) {
    return { root: previous.root, policyFile: path.join(previous.root, POLICY_RELATIVE_PATH) };
  }

  if (!prompt) return null;
  const roots = [cwd, path.join(cwd, ".worktrees")];
  for (const parent of roots) {
    let entries = [];
    try {
      entries = fs.readdirSync(parent, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const root = path.join(parent, entry.name);
      const policyFile = path.join(root, POLICY_RELATIVE_PATH);
      const policy = readJson(policyFile);
      if (policy && policyMatchesPrompt(policy, prompt)) return { root, policyFile };
    }
  }
  return null;
}

function run(command, args, options = {}) {
  try {
    return execFileSync(command, args, {
      cwd: options.cwd,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      timeout: options.timeout || 1_500,
    }).trim();
  } catch {
    return "";
  }
}

function git(root, args) {
  return run("git", ["-C", root, ...args], { timeout: 800 });
}

/**
 * rebase·merge·cherry-pick·revert 가 진행 중인지. 진행 중이면 HEAD 가 DETACHED 이고
 * 충돌 해결을 위한 파일 편집이 필요하다. 이를 "보호 브랜치 직접 수정"으로 막으면
 * 작업에서 빠져나올 수 없다.
 */
function sequencerInProgress(root) {
  const gitDir = run("git", ["-C", root, "rev-parse", "--git-dir"], { timeout: 500 });
  if (!gitDir) return false;
  const base = path.isAbsolute(gitDir) ? gitDir : path.join(root, gitDir);
  return ["rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD"].some((entry) =>
    fs.existsSync(path.join(base, entry)),
  );
}

function validatePolicy(policy) {
  return Boolean(
    policy &&
      policy.version === 1 &&
      policy.project &&
      (policy.developmentSupabaseProjectRef || policy.productionSupabaseProjectRef) &&
      Array.isArray(policy.protectedBranches),
  );
}

function hash(value) {
  return crypto.createHash("sha256").update(value).digest("hex").slice(0, 20);
}

function cacheRoot() {
  return (
    process.env.AGENT_GUARD_CACHE_DIR ||
    path.join(os.homedir(), ".cache", "ai-working-preview-db-guard")
  );
}

function sessionFile(input) {
  const id = String(input.session_id || "unknown").replace(/[^a-zA-Z0-9_.-]/g, "_");
  return path.join(cacheRoot(), "sessions", `${id}.json`);
}

function parseSupabaseRef(url) {
  const match = String(url || "").match(/^https:\/\/([a-z0-9]+)\.supabase\.(?:co|in)(?:\/|$)/i);
  return match?.[1] || "";
}

function readEnvMode(root, policy) {
  const candidates = [path.join(root, ".env.local")];
  const apps = path.join(root, "apps");
  try {
    for (const entry of fs.readdirSync(apps, { withFileTypes: true })) {
      if (entry.isDirectory()) candidates.push(path.join(apps, entry.name, ".env.local"));
    }
  } catch {
    // Not a monorepo.
  }

  let sawBranch = false;
  let sawLocal = false;
  for (const file of candidates) {
    let content = "";
    try {
      content = fs.readFileSync(file, "utf8");
    } catch {
      continue;
    }
    const match = content.match(/^NEXT_PUBLIC_SUPABASE_URL\s*=\s*["']?([^\s"']+)/m);
    if (!match) continue;
    const value = match[1];
    if (/^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/i.test(value)) sawLocal = true;
    const ref = parseSupabaseRef(value);
    if (ref && ref === policy.developmentSupabaseProjectRef) sawBranch = true;
    else if (ref && ref === policy.productionSupabaseProjectRef) return "production";
    if (ref) sawBranch = true;
  }
  if (sawBranch) return "branch";
  if (sawLocal) return "local";
  return "missing";
}

function remoteSnapshot(root, policy, branch, head) {
  if (process.env.AGENT_GUARD_SKIP_REMOTE === "1") {
    return { state: "unverified", reason: "remote-check-disabled" };
  }

  const file = path.join(cacheRoot(), "remote", `${hash(`${root}:${branch}:${head}`)}.json`);
  const cached = readJson(file);
  if (cached && Date.now() - cached.checkedAt < REMOTE_CACHE_TTL_MS) return cached;

  const prRaw = run(
    "gh",
    ["pr", "list", "--state", "open", "--head", branch, "--limit", "1", "--json", "number,url,baseRefName,headRefName"],
    { cwd: root },
  );
  let pr = null;
  try {
    pr = JSON.parse(prRaw || "[]")[0] || null;
  } catch {
    pr = null;
  }

  // 공유 develop DB 전략에서는 PR 별 branch DB 가 존재하지 않는다.
  // 조회해봐야 항상 preview-missing 이고, 매 턴 느린 CLI 호출만 남는다.
  const needsRemoteBranch =
    policy.previewDatabaseRequired !== false && (Boolean(pr) || branch === policy.developBranch);
  if (!needsRemoteBranch) {
    const result = { checkedAt: Date.now(), state: "local-only", pr: null, branchDb: null };
    writeJson(file, result);
    return result;
  }

  const branchesRaw = run(
    "supabase",
    ["branches", "list", "--project-ref", policy.productionSupabaseProjectRef, "-o", "json"],
    { cwd: root, timeout: 2_500 },
  );
  if (!branchesRaw) {
    const result = { checkedAt: Date.now(), state: "unverified", pr, branchDb: null };
    writeJson(file, result);
    return result;
  }

  let branches = [];
  try {
    branches = JSON.parse(branchesRaw);
  } catch {
    branches = [];
  }
  const branchDb = branches.find(
    (item) => item.git_branch === branch || item.name === branch,
  );
  const status = String(branchDb?.status || "UNKNOWN").toUpperCase();
  const state = !branchDb
    ? "preview-missing"
    : READY_STATUSES.has(status)
      ? "preview-ready"
      : status.includes("FAIL") || status.includes("ERROR")
        ? "preview-failed"
        : "preview-pending";
  const result = {
    checkedAt: Date.now(),
    state,
    pr: pr ? { number: pr.number, baseRefName: pr.baseRefName } : null,
    branchDb: branchDb
      ? { status, projectRefMatchesProduction: branchDb.project_ref === policy.productionSupabaseProjectRef }
      : null,
  };
  writeJson(file, result);
  return result;
}

function buildState(root, policy, includeRemote, previousState = null) {
  const branch = git(root, ["branch", "--show-current"]) || "DETACHED";
  const head = git(root, ["rev-parse", "HEAD"]) || "UNKNOWN";
  const protectedBranch = policy.protectedBranches.includes(branch) || branch === "DETACHED";
  const envMode = readEnvMode(root, policy);
  const reusableRemote =
    previousState?.root === root &&
    previousState?.branch === branch &&
    previousState?.head === head &&
    previousState?.remote;
  const remote = includeRemote
    ? remoteSnapshot(root, policy, branch, head)
    : reusableRemote || { state: "unverified", reason: "missing-turn-check" };
  return { root, branch, head, protectedBranch, envMode, remote, checkedAt: Date.now() };
}

function stateContext(policy, state) {
  const lines = [
    `[Preview DB Guard: ${policy.project}]`,
    `branch=${state.branch} local_env=${state.envMode} preview=${state.remote.state}`,
  ];
  if (state.protectedBranch) {
    lines.push("BLOCKED_FOR_WRITES: main/develop/detached에서 수정하지 말고 develop 기준 feat/* 브랜치를 먼저 만든다.");
  } else if (state.envMode === "production") {
    lines.push("PRODUCTION_ENV_DETECTED: 이 feature branch에서 dev/build/test를 실행하지 말고 local 또는 branch DB env로 교체한다.");
  } else if (policy.previewDatabaseRequired === false) {
    lines.push("SINGLE_DEVELOPMENT_DB: Supabase Branching을 쓰지 않는다. 모든 Preview가 정책의 단일 개발 프로젝트를 본다.");
  } else if (state.remote.state === "local-only") {
    lines.push("LOCAL_ONLY: 코드 편집은 가능하지만 로컬 Supabase만 사용한다. Preview는 PR 생성 후 branch DB READY 확인 전 실행·배포하지 않는다.");
  } else if (state.remote.state === "preview-ready") {
    lines.push("PREVIEW_READY: 대응하는 격리 Supabase branch DB가 확인됐다. production ref 사용은 계속 금지한다.");
  } else {
    lines.push("PREVIEW_UNVERIFIED: branch DB가 READY임을 증명할 때까지 Preview 실행·배포를 중단한다. production fallback 금지.");
  }
  lines.push("Release: feat/*→develop 통합, develop→main merge에서만 production migration/deploy. 직접 production db push 금지.");
  return lines.join("\n");
}

function deny(reason) {
  process.stdout.write(
    `${JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: `Preview DB Guard: ${reason}`,
      },
    })}\n`,
  );
}

function inputTargetsProject(input, state) {
  const toolInput = input.tool_input || {};
  const explicitDir = toolInput.workdir || toolInput.cwd;
  if (explicitDir) {
    const inputCwd = path.resolve(input.cwd || process.cwd());
    return isInside(path.resolve(inputCwd, explicitDir), state.root);
  }
  if (isInside(path.resolve(input.cwd || process.cwd()), state.root)) return true;
  const serialized = JSON.stringify(toolInput);
  return serialized.includes(state.root) || serialized.includes(`${path.basename(state.root)}/`);
}

function isMutationCommand(command) {
  const patterns = [
    /\bgit\s+(?:add|commit|push|merge|rebase|cherry-pick)\b/i,
    /\b(?:npm|pnpm|yarn)\s+(?:install|add|remove|uninstall)\b/i,
    /\bsupabase\s+migration\s+new\b/i,
    /\b(?:sed|perl)\s+-[^\s]*i\b/i,
    /\b(?:tee|touch|mkdir|mv|cp|rm)\b/i,
    /(^|[^<>])>{1,2}(?!=)/,
  ];
  return patterns.some((pattern) => pattern.test(command));
}

// branching.md 단일 개발 DB 전략(2026-08-13)의 개발 DB 수동 적용 경로.
// 네 조건 전부 충족 시에만 db push 를 허용한다:
// ① 명령 '맨 앞' CONFIRMED=1 앵커(부분문자열 우회 차단, pre-tool.sh 와 동일 기준)
// ② 정책이 단일 개발 프로젝트 모드(previewDatabaseRequired=false 또는
//    branchingStrategy.mode="disabled-single-project") + developmentSupabaseProjectRef 보유
// ③ 로컬 env 가 production 을 가리키지 않음
// ④ push 대상 workdir(--workdir 또는 state.root)가 정책의 개발 project ref 에 link 됨
//    (link 파일 부재 = 검증 불가 = 차단. production Supabase ref 로는 절대 통과 불가)
function isConfirmedDevelopmentDbPush(command, input, policy, state) {
  if (!/^\s*CONFIRMED=1\s/.test(command)) return false;
  const singleDevProject =
    policy.previewDatabaseRequired === false ||
    policy.branchingStrategy?.mode === "disabled-single-project";
  if (!singleDevProject || !policy.developmentSupabaseProjectRef) return false;
  if (state.envMode === "production") return false;
  const workdirMatch = command.match(/--workdir(?:=|\s+)(?:"([^"]+)"|'([^']+)'|(\S+))/);
  const workdir = workdirMatch ? workdirMatch[1] || workdirMatch[2] || workdirMatch[3] : null;
  const root = workdir ? path.resolve(input.cwd || process.cwd(), workdir) : state.root;
  let linkedRef = "";
  try {
    linkedRef = fs.readFileSync(path.join(root, "supabase", ".temp", "project-ref"), "utf8").trim();
  } catch {
    return false;
  }
  return linkedRef === policy.developmentSupabaseProjectRef;
}

const VERCEL_LAUNCH = String.raw`(?:^|[;&|]\s*|\(\s*)(?:(?:npx|pnpm\s+dlx|yarn\s+dlx)\s+)?vercel`;

// True only when vercel runs as a command, not when the word appears as an
// argument or inside a string (grep vercel, cat vercel.json, ...).
function isVercelInvocation(command) {
  return new RegExp(`${VERCEL_LAUNCH}(?:\\s|$|[;&|])`, "i").test(command);
}

// Anything that can change what production serves. Always denied from a
// developer machine — production goes out through develop → main merge only.
function isVercelProductionMutation(command) {
  if (!isVercelInvocation(command)) return false;
  const productionSubcommand = new RegExp(
    `${VERCEL_LAUNCH}\\s+(?:(?:--?[^\\s]+\\s+)*)(?:promote|rollback|alias)\\b`,
    "i",
  );
  const productionEnvMutation =
    new RegExp(`${VERCEL_LAUNCH}\\s+env\\s+(?:add|rm|remove)\\b`, "i").test(command) &&
    /\bproduction\b/i.test(command);
  const productionTarget = /(?:--prod\b|--target[= ]production\b)/i.test(command);
  return productionSubcommand.test(command) || productionEnvMutation || productionTarget;
}

// Preview deployments. Allowed unless the local env points at production, or the
// project still requires a per-PR branch DB that is not READY yet.
// Read-only calls (whoami, teams, projects, link, ls, inspect, logs, env pull/ls)
// are never gated: local env bootstrap pulls development variables from Vercel.
function isVercelPreviewDeploy(command) {
  const deploySubcommand = new RegExp(
    `${VERCEL_LAUNCH}\\s+(?:(?:--?[^\\s]+\\s+)*)(?:deploy|build|redeploy)\\b`,
    "i",
  );
  const bareInvocation = new RegExp(`${VERCEL_LAUNCH}(?:\\s+--?[^\\s]+)*\\s*(?:$|[;&|])`, "i");
  return deploySubcommand.test(command) || bareInvocation.test(command);
}

function isAppExecution(command) {
  return /\b(?:next\s+(?:dev|build)|turbo\s+(?:dev|build|test)|playwright\s+test|(?:npm|pnpm|yarn)\s+(?:run\s+)?(?:dev|build|test|e2e))\b/i.test(
    command,
  );
}

async function main() {
  const input = await readStdin();
  const event = input.hook_event_name || "";
  if (!['UserPromptSubmit', 'PreToolUse'].includes(event)) return;

  const sFile = sessionFile(input);
  const discovered = discoverPolicy(path.resolve(input.cwd || process.cwd()), input.prompt || "", sFile);
  if (!discovered) return;
  const policy = readJson(discovered.policyFile);
  if (!validatePolicy(policy)) {
    if (event === "UserPromptSubmit") {
      process.stdout.write(`${JSON.stringify({ systemMessage: `Preview DB Guard policy invalid: ${discovered.policyFile}` })}\n`);
    }
    return;
  }

  const previousState = readJson(sFile);
  const state = buildState(
    discovered.root,
    policy,
    event === "UserPromptSubmit",
    previousState,
  );
  writeJson(sFile, state);

  if (event === "UserPromptSubmit") {
    process.stdout.write(
      `${JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "UserPromptSubmit",
          additionalContext: stateContext(policy, state),
        },
      })}\n`,
    );
    return;
  }

  if (!inputTargetsProject(input, state)) return;
  const tool = input.tool_name || "";
  const command = String(input.tool_input?.command || "");
  const editTool = /^(?:apply_patch|Edit|Write)$/.test(tool);

  // rebase/cherry-pick 진행 중에는 HEAD 가 항상 DETACHED 다. 그 상태를 "보호 브랜치 직접
  // 수정"으로 취급하면 충돌 해결(편집)도, 진행·중단 명령도 막혀 빠져나올 수 없다(교착).
  // 진행 중일 때만 예외를 열고, 그 밖의 DETACHED 는 그대로 차단한다.
  const inSequencer = state.protectedBranch && sequencerInProgress(state.root);

  if (
    state.protectedBranch &&
    !inSequencer &&
    (editTool || (tool === "Bash" && isMutationCommand(command)))
  ) {
    deny(`${state.branch} 직접 수정 차단. develop 기준 feat/* 브랜치를 만든 뒤 다시 실행한다.`);
    return;
  }
  if (tool === "Bash" && /\bsupabase\s+db\s+push\b/i.test(command) && !/--dry-run\b/.test(command)) {
    if (!isConfirmedDevelopmentDbPush(command, input, policy, state)) {
      deny(
        "직접 db push 차단. 개발 DB 반영은 'CONFIRMED=1 supabase db push --workdir <repo>'만 허용" +
          "(단일 개발 프로젝트 정책 + 개발 ref link + 비-production env, branching.md). 운영은 develop→main merge 경로.",
      );
      return;
    }
  }
  if (tool === "Bash" && isVercelProductionMutation(command)) {
    deny("production 배포·변경 직접 실행 차단. develop→main merge 경로를 사용한다.");
    return;
  }
  if (tool === "Bash" && isVercelPreviewDeploy(command)) {
    if (state.envMode === "production") {
      deny("Preview 배포 환경이 production Supabase를 가리킨다. develop DB env로 교체한다.");
      return;
    }
    // previewDatabaseRequired=false 인 프로젝트는 PR 별 ephemeral DB 를 만들지 않고
    // 공유 develop DB 를 쓴다. 그런 프로젝트에 branch DB READY 를 요구하면
    // 모든 Preview 가 영구히 막힌다.
    if (policy.previewDatabaseRequired !== false && state.remote.state !== "preview-ready") {
      deny("Supabase branch DB READY 확인 전 Preview 배포를 실행할 수 없다.");
      return;
    }
  }
  if (tool === "Bash" && state.envMode === "production" && isAppExecution(command)) {
    deny("feature 작업 환경이 production Supabase를 가리킨다. local/branch env로 교체하기 전 dev/build/test 실행 금지.");
  }
}

main().catch(() => process.exit(0));
