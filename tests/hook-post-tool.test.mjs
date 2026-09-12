import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import test from "node:test"
import { execFileSync } from "node:child_process"

// post-tool.sh의 dev-protocol 게이트 감지 검증.
// 실제 HOME을 오염시키지 않도록 fake HOME 아래에 .claude/hooks(lib.sh)와 project repo를 구성한다.
const script = path.resolve("hooks/post-tool.sh")
const libSource = path.resolve("hooks/lib.sh")

function makeHome() {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), "post-tool-test-"))
  fs.mkdirSync(path.join(home, ".claude", "hooks"), { recursive: true })
  fs.copyFileSync(libSource, path.join(home, ".claude", "hooks", "lib.sh"))
  return home
}

function makeProjectRepo(home, name) {
  const repo = path.join(home, "projects", name)
  fs.mkdirSync(path.join(repo, "src"), { recursive: true })
  // 브랜치 가드 간섭을 피하려고 feature 브랜치로 init (게이트 감지만 검증).
  execFileSync("git", ["init", "-q", "-b", "feat/test", repo])
  const src = path.join(repo, "src", "widget.ts")
  fs.writeFileSync(src, "export const widget = 1\n")
  return { repo, src }
}

function invoke(home, filePath, sessionId) {
  const output = execFileSync("/bin/sh", [script], {
    input: JSON.stringify({ session_id: sessionId, tool_input: { file_path: filePath } }),
    encoding: "utf8",
    env: { ...process.env, HOME: home, AI_WORKING_PROJECTS_ROOT: path.join(home, "projects") },
  }).trim()
  return output ? JSON.parse(output).hookSpecificOutput.additionalContext : ""
}

test("dev-protocol gate detection in post-tool.sh", () => {
  const home = makeHome()
  const { repo, src } = makeProjectRepo(home, "proj-a")

  // ① 구현노트 없이 aidp 앱 소스 편집 → 게이트 안내 1회
  const first = invoke(home, src, "sess-1")
  assert.match(first, /\[dev-protocol\]/, "구현노트 없으면 게이트 안내가 나와야 한다")

  // ② 같은 세션 두 번째 편집 → 스탬프로 침묵 (세션×repo당 1회)
  const second = invoke(home, src, "sess-1")
  assert.doesNotMatch(second, /\[dev-protocol\]/, "같은 세션에서는 반복 경고하지 않는다")

  // ③ 새 세션이라도 최근 갱신된 구현노트가 있으면 침묵
  const notes = path.join(repo, "docs", "impl-notes")
  fs.mkdirSync(notes, { recursive: true })
  fs.writeFileSync(path.join(notes, "2026-08-27-feature.md"), "# note\n")
  const withNote = invoke(home, src, "sess-2")
  assert.doesNotMatch(withNote, /\[dev-protocol\]/, "fresh 구현노트가 있으면 경고하지 않는다")

  // ④ the configured project workspace 밖의 소스 편집은 대상 아님
  const outside = path.join(home, "other", "src")
  fs.mkdirSync(outside, { recursive: true })
  const outsideFile = path.join(outside, "widget.ts")
  fs.writeFileSync(outsideFile, "export const widget = 2\n")
  const outsideOut = invoke(home, outsideFile, "sess-3")
  assert.doesNotMatch(outsideOut, /\[dev-protocol\]/, "aidp 밖 파일은 게이트 대상이 아니다")

  // ⑤ 앱 소스 확장자가 아니면(md 등) 대상 아님 — 노트 없는 새 repo에서 확인
  const { repo: repoB } = makeProjectRepo(home, "proj-b")
  const doc = path.join(repoB, "README.md")
  fs.writeFileSync(doc, "# readme\n")
  const docOut = invoke(home, doc, "sess-4")
  assert.doesNotMatch(docOut, /\[dev-protocol\]/, "문서 파일은 게이트 대상이 아니다")

  fs.rmSync(home, { recursive: true, force: true })
})
