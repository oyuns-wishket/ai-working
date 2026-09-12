import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";

const script = path.resolve("hooks/preview-db-guard.mjs");
const temp = fs.mkdtempSync(path.join(os.tmpdir(), "preview-db-guard-test-"));
const repo = path.join(temp, "example-erp");
const cache = path.join(temp, "cache");

function runGit(...args) {
  execFileSync("git", args, { cwd: repo, stdio: "ignore" });
}

function invoke(payload, extraEnv = {}) {
  const output = execFileSync(process.execPath, [script], {
    cwd: repo,
    input: JSON.stringify(payload),
    encoding: "utf8",
    env: {
      ...process.env,
      AGENT_GUARD_POLICY_ROOT: repo,
      AGENT_GUARD_CACHE_DIR: cache,
      AGENT_GUARD_SKIP_REMOTE: "1",
      ...extraEnv,
    },
  }).trim();
  return output ? JSON.parse(output) : null;
}

try {
  fs.mkdirSync(path.join(repo, ".agent"), { recursive: true });
  fs.writeFileSync(
    path.join(repo, ".agent", "preview-db-policy.json"),
    JSON.stringify({
      version: 1,
      project: "Example ERP",
      aliases: ["example-erp"],
      productionSupabaseProjectRef: "prodref123",
      protectedBranches: ["main", "develop"],
      developBranch: "develop",
    }),
  );
  fs.writeFileSync(path.join(repo, "README.md"), "fixture\n");
  runGit("init", "-b", "main");
  runGit("config", "user.email", "fixture@example.com");
  runGit("config", "user.name", "Fixture");
  runGit("add", ".");
  runGit("commit", "-m", "fixture");

  const prompt = invoke({
    session_id: "session-main",
    cwd: repo,
    hook_event_name: "UserPromptSubmit",
    prompt: "Example ERP 수정",
  });
  assert.match(prompt.hookSpecificOutput.additionalContext, /BLOCKED_FOR_WRITES/);

  const blockedEdit = invoke({
    session_id: "session-main",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "apply_patch",
    tool_input: { command: "*** Update File: README.md" },
  });
  assert.equal(blockedEdit.hookSpecificOutput.permissionDecision, "deny");

  runGit("switch", "-c", "feat/safe-preview");
  const featurePrompt = invoke({
    session_id: "session-feature",
    cwd: repo,
    hook_event_name: "UserPromptSubmit",
    prompt: "계속",
  });
  assert.doesNotMatch(featurePrompt.hookSpecificOutput.additionalContext, /BLOCKED_FOR_WRITES/);

  const blockedPreview = invoke({
    session_id: "session-feature",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "vercel deploy" },
  });
  assert.equal(blockedPreview.hookSpecificOutput.permissionDecision, "deny");

  const head = execFileSync("git", ["rev-parse", "HEAD"], {
    cwd: repo,
    encoding: "utf8",
  }).trim();
  fs.mkdirSync(path.join(cache, "sessions"), { recursive: true });
  fs.writeFileSync(
    path.join(cache, "sessions", "session-feature.json"),
    JSON.stringify({
      root: repo,
      branch: "feat/safe-preview",
      head,
      remote: { state: "preview-ready" },
    }),
  );
  fs.writeFileSync(
    path.join(repo, ".env.local"),
    "NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321\n",
  );
  const allowedPreview = invoke({
    session_id: "session-feature",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "vercel deploy" },
  });
  assert.equal(allowedPreview, null);

  fs.writeFileSync(
    path.join(repo, ".env.local"),
    "NEXT_PUBLIC_SUPABASE_URL=https://prodref123.supabase.co\n",
  );
  const blockedDev = invoke({
    session_id: "session-feature",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "npm run dev" },
  });
  assert.equal(blockedDev.hookSpecificOutput.permissionDecision, "deny");
  assert.match(blockedDev.hookSpecificOutput.permissionDecisionReason, /production Supabase/);

  const blockedPush = invoke({
    session_id: "session-feature",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "CONFIRMED=1 supabase db push" },
  });
  assert.equal(blockedPush.hookSpecificOutput.permissionDecision, "deny");

  // 단일 개발 DB 전략(branching.md): CONFIRMED=1 + 개발 ref link + 비-production env → 허용.
  fs.writeFileSync(
    path.join(repo, ".agent", "preview-db-policy.json"),
    JSON.stringify({
      version: 1,
      project: "Example ERP",
      aliases: ["example-erp"],
      productionSupabaseProjectRef: null,
      developmentSupabaseProjectRef: "devref456",
      previewDatabaseRequired: false,
      branchingStrategy: { mode: "disabled-single-project" },
      protectedBranches: ["main", "develop"],
      developBranch: "develop",
    }),
  );
  fs.writeFileSync(
    path.join(repo, ".env.local"),
    "NEXT_PUBLIC_SUPABASE_URL=https://devref456.supabase.co\n",
  );

  // link 파일이 없으면 검증 불가 → 여전히 차단
  const pushWithoutLink = invoke({
    session_id: "session-feature",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "CONFIRMED=1 supabase db push" },
  });
  assert.equal(pushWithoutLink.hookSpecificOutput.permissionDecision, "deny");

  fs.mkdirSync(path.join(repo, "supabase", ".temp"), { recursive: true });
  fs.writeFileSync(path.join(repo, "supabase", ".temp", "project-ref"), "devref456\n");

  // CONFIRMED=1 앵커 없이는 차단 (부분문자열 우회 차단)
  const pushWithoutConfirm = invoke({
    session_id: "session-feature",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "supabase db push" },
  });
  assert.equal(pushWithoutConfirm.hookSpecificOutput.permissionDecision, "deny");
  const pushEmbeddedConfirm = invoke({
    session_id: "session-feature",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "cd /tmp && CONFIRMED=1 supabase db push" },
  });
  assert.equal(pushEmbeddedConfirm.hookSpecificOutput.permissionDecision, "deny");

  // 네 조건 전부 충족 → 통과
  const allowedPush = invoke({
    session_id: "session-feature",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "CONFIRMED=1 supabase db push" },
  });
  assert.equal(allowedPush, null);

  // --workdir 로 지정한 경로의 link ref 가 다르면 차단
  const otherDir = path.join(temp, "other-project");
  fs.mkdirSync(path.join(otherDir, "supabase", ".temp"), { recursive: true });
  fs.writeFileSync(path.join(otherDir, "supabase", ".temp", "project-ref"), "prodref123\n");
  const pushWrongWorkdir = invoke({
    session_id: "session-feature",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: `CONFIRMED=1 supabase db push --workdir ${otherDir}` },
  });
  assert.equal(pushWrongWorkdir.hookSpecificOutput.permissionDecision, "deny");

  // --workdir 가 개발 ref 에 link 된 워크트리면 통과
  const allowedWorkdirPush = invoke({
    session_id: "session-feature",
    cwd: repo,
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: `CONFIRMED=1 supabase db push --workdir ${repo}` },
  });
  assert.equal(allowedWorkdirPush, null);

  process.stdout.write("preview-db-guard: 13 scenarios passed\n");
} finally {
  fs.rmSync(temp, { recursive: true, force: true });
}
