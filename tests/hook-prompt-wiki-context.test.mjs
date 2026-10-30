import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import test from "node:test"
import { execFileSync } from "node:child_process"

const hook = path.resolve("hooks", "prompt-wiki-context.mjs")

function fixture(routeJson) {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), "prompt-wiki-"))
  const scripts = path.join(home, ".claude", "skills", "project-wiki-context", "scripts")
  fs.mkdirSync(scripts, { recursive: true })
  // Stub resolver: prints a fixed route result, records the query it received.
  fs.writeFileSync(path.join(scripts, "wiki_context.py"),
    `import json,sys\nopen(${JSON.stringify(path.join(home, "query.txt"))},"w").write(sys.argv[sys.argv.index("--query")+1])\nprint(json.dumps(${JSON.stringify(routeJson)}))\n`)
  return home
}

function run(home, input) {
  const env = { ...process.env, HOME: home }
  delete env.AI_WORKING_PROMPT_WIKI
  return execFileSync("node", [hook], { input: JSON.stringify(input), env, encoding: "utf8" })
}

const routed = { mode: "wiki-bounded", wiki_root: "/w", retrieval_feedback: { trace_id: "t1" },
  documents: [{ relative_path: "sys-wiki/aidp/gj/a.md", title: "GJ 규칙", type: "domain", read_mode: "document", score: 90 },
              { relative_path: "my-wiki/m.md", title: "메모", corpus: "manual", read_mode: "document", score: 60 }] }

test("connected project prompt gets document titles and paths, not bodies", () => {
  const home = fixture(routed)
  const out = JSON.parse(run(home, { prompt: "이카운트 컷오버 최종 보고 정리해줘", cwd: "/p", session_id: "s1" }))
  const text = out.hookSpecificOutput.additionalContext
  assert.equal(out.hookSpecificOutput.hookEventName, "UserPromptSubmit")
  assert.match(text, /GJ 규칙 \[domain\]\n  \/w\/sys-wiki\/aidp\/gj\/a\.md/)
  assert.match(text, /메모 \[내 메모\]/)
  assert.match(text, /trace t1/)
  fs.rmSync(home, { recursive: true, force: true })
})

test("the same documents are not repeated within a session", () => {
  const home = fixture(routed)
  run(home, { prompt: "이카운트 컷오버 최종 보고 정리해줘", cwd: "/p", session_id: "s2" })
  assert.equal(run(home, { prompt: "이카운트 컷오버 다른 질문 하나 더", cwd: "/p", session_id: "s2" }), "")
  fs.rmSync(home, { recursive: true, force: true })
})

test("short prompts, slash commands, opt-out and unconnected projects stay silent", () => {
  const home = fixture(routed)
  assert.equal(run(home, { prompt: "ㅇㅋ", cwd: "/p", session_id: "s3" }), "")
  assert.equal(run(home, { prompt: "/code-review high please", cwd: "/p", session_id: "s3" }), "")
  const env = { ...process.env, HOME: home, AI_WORKING_PROMPT_WIKI: "0" }
  assert.equal(execFileSync("node", [hook], { input: JSON.stringify({ prompt: "충분히 긴 요청 문장입니다 정말로", cwd: "/p" }), env, encoding: "utf8" }), "")
  const other = fixture({ mode: "repo-only", documents: [] })
  assert.equal(run(other, { prompt: "충분히 긴 요청 문장입니다 정말로", cwd: "/p", session_id: "s4" }), "")
  fs.rmSync(home, { recursive: true, force: true }); fs.rmSync(other, { recursive: true, force: true })
})

test("pasted code blocks are stripped from the routing query", () => {
  const home = fixture(routed)
  run(home, { prompt: "이 에러 원인 봐줘\n```\nTraceback huge log\n```\n세금계산서 발행", cwd: "/p", session_id: "s5" })
  const query = fs.readFileSync(path.join(home, "query.txt"), "utf8")
  assert.doesNotMatch(query, /Traceback/)
  assert.match(query, /세금계산서 발행/)
  fs.rmSync(home, { recursive: true, force: true })
})

test("each document line carries the note's own summary so relevance is visible without opening it", () => {
  const wiki = fs.mkdtempSync(path.join(os.tmpdir(), "prompt-wiki-root-"))
  const home = fixture({ ...routed, wiki_root: wiki })
  fs.mkdirSync(path.join(wiki, "sys-wiki/aidp/gj"), { recursive: true })
  fs.writeFileSync(path.join(wiki, "sys-wiki/aidp/gj/a.md"),
    "---\ntitle: \"GJ 규칙\"\n---\n\n# GJ 규칙\n\n> 세금계산서는 종사업장 번호로 발행한다.\n\n## 핵심 지식\n")
  fs.mkdirSync(path.join(wiki, "my-wiki"), { recursive: true })
  fs.writeFileSync(path.join(wiki, "my-wiki/m.md"), "# 메모\n\n## 요약\n\n" + "가".repeat(400) + "\n")
  const text = JSON.parse(run(home, { prompt: "이카운트 컷오버 최종 보고 정리해줘", cwd: "/p", session_id: "s6" })).hookSpecificOutput.additionalContext
  assert.match(text, /GJ 규칙 \[domain\] — 세금계산서는 종사업장 번호로 발행한다\./)
  assert.match(text, /메모 \[내 메모\] — 가{150,159}…/)
  assert.match(text, /설계·구현 결정 전에 Read로 읽으세요/)
  fs.rmSync(home, { recursive: true, force: true }); fs.rmSync(wiki, { recursive: true, force: true })
})

test("a multi-session lane prompt is routed by its task section, not its boilerplate", () => {
  const home = fixture(routed)
  const lane = "# Lane `ux` of task `t`\n\nYou are one lane session spawned by a Lead session.\n\n## Where you are\n\n- Repository: /tmp/x\n\n## Acceptance criteria\n\n- 발주서에 배송 구간 칼럼이 보인다\n\n## Task\n\n도선료 정산 로직을 고친다.\n\n## Return format\n\nJSON only.\n"
  run(home, { prompt: lane, cwd: "/p", session_id: "s7" })
  const query = fs.readFileSync(path.join(home, "query.txt"), "utf8")
  assert.match(query, /배송 구간 칼럼/)
  assert.match(query, /도선료 정산 로직/)
  assert.doesNotMatch(query, /Lead session|Return format|JSON only/)
  fs.rmSync(home, { recursive: true, force: true })
})

test("weak matches below the score floor are not offered", () => {
  const home = fixture({ ...routed, documents: [
    { relative_path: "sys-wiki/aidp/gj/strong.md", title: "강한 일치", type: "domain", score: 70 },
    { relative_path: "sys-wiki/aidp/gj/weak.md", title: "약한 일치", type: "domain", score: 30 }] })
  const text = JSON.parse(run(home, { prompt: "이카운트 컷오버 최종 보고 정리해줘", cwd: "/p", session_id: "s8" })).hookSpecificOutput.additionalContext
  assert.match(text, /강한 일치/)
  assert.doesNotMatch(text, /약한 일치/)
  const generic = fixture({ ...routed, documents: [{ relative_path: "sys-wiki/x.md", title: "x", score: 30 }] })
  assert.equal(run(generic, { prompt: "커밋하고 PR 올려줘 지금 바로", cwd: "/p", session_id: "s9" }), "")
  fs.rmSync(home, { recursive: true, force: true }); fs.rmSync(generic, { recursive: true, force: true })
})

test("an English prompt that names issues is enriched with their titles", () => {
  const home = fixture(routed)
  const bin = path.join(home, "bin"); fs.mkdirSync(bin)
  fs.writeFileSync(path.join(bin, "gh"), "#!/bin/sh\n[ \"$3\" = 1754 ] && echo '유통 발주 택배비 매입정산 연결'\n", { mode: 0o755 })
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "prompt-wiki-cwd-"))
  const env = { ...process.env, HOME: home, PATH: `${bin}:${process.env.PATH}` }
  delete env.AI_WORKING_PROMPT_WIKI
  execFileSync("node", [hook], { input: JSON.stringify({ prompt: "Fix #1754 supplier-only purchase settlement shipping once", cwd: dir, session_id: "s10" }), env, encoding: "utf8" })
  assert.match(fs.readFileSync(path.join(home, "query.txt"), "utf8"), /^유통 발주 택배비 매입정산 연결 Fix #1754/)
  fs.rmSync(home, { recursive: true, force: true }); fs.rmSync(dir, { recursive: true, force: true })
})

test("system-generated turns (task notifications, cross-session messages, interruptions) are not routed", () => {
  const home = fixture(routed)
  for (const prompt of [
    "<task-notification>\n<task-id>abc</task-id>\n<summary>Background command finished with lots of text</summary>\n</task-notification>",
    "<cross-session-message from=\"worker\">이카운트 컷오버 최종 보고 정리해줘</cross-session-message>",
    "[Request interrupted by user for tool use] 이카운트 컷오버 최종 보고 정리해줘",
  ]) assert.equal(run(home, { prompt, cwd: "/p", session_id: "s11" }), "", prompt.slice(0, 20))
  assert.notEqual(run(home, { prompt: "이카운트 컷오버 최종 보고 정리해줘", cwd: "/p", session_id: "s11" }), "")
  fs.rmSync(home, { recursive: true, force: true })
})
