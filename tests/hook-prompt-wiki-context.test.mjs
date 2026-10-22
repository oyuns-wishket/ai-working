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
  documents: [{ relative_path: "sys-wiki/aidp/gj/a.md", title: "GJ 규칙", type: "domain", read_mode: "document" },
              { relative_path: "my-wiki/m.md", title: "메모", corpus: "manual", read_mode: "document" }] }

test("connected project prompt gets document titles and paths, not bodies", () => {
  const home = fixture(routed)
  const out = JSON.parse(run(home, { prompt: "이카운트 컷오버 최종 보고 정리해줘", cwd: "/p", session_id: "s1" }))
  const text = out.hookSpecificOutput.additionalContext
  assert.equal(out.hookSpecificOutput.hookEventName, "UserPromptSubmit")
  assert.match(text, /GJ 규칙 \[domain\] \/w\/sys-wiki\/aidp\/gj\/a\.md/)
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
