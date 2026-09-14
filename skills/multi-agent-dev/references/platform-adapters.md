# Platform adapters

Skill의 역할 이름은 agent-neutral이다. 현재 플랫폼의 native mechanism으로 번역한다.

## Claude native subagents

- Use native subagents directly; no orchestration plugin is required.
- Use `Explore` for bounded read-only discovery when available, and `general-purpose` for implementation or an independently scoped review/verification task. Pass repository guidance explicitly to read-only built-ins that do not inherit it. A role is a task contract, not a requirement for a same-named plugin agent.
- Reuse a more specific project `.claude/agents/*.md` worker when its capability and restrictions fit. Do not rewrite project workers during global environment maintenance.
- The lead passes the task, working directory, allowed files, read/write scope and required evidence. Give reviewers the raw diff and acceptance criteria; they must not edit the implementation they review. This is a workflow restriction, not an OS sandbox claim; when enforced read-only access is needed, use a native agent with an explicit read-tool allowlist or a read-only sandbox.
- Prefer existing native agent types; if unavailable, use a separate native session with the same contract. Do not install a plugin merely to satisfy an old role name.
- Claude workers inherit the lead effort. Pin write workers to their assigned isolated worktree; never assume a plugin created one.

## Codex

- built-in `explorer`, `worker`, `default`가 충분하면 재사용한다.
- 프로젝트 `.codex/agents/*.toml`이 같은 역량에 더 구체적이면 프로젝트 Worker를 우선한다.
- 읽기 Worker는 `sandbox_mode = "read-only"`, 쓰기 Worker는 `sandbox_mode = "workspace-write"`로 렌더한다.
- 기본 Worker reasoning effort는 `high`; DB, security, final review처럼 고위험이고 지원되는 모델이면 `xhigh`를 사용할 수 있다.
- Lead가 subagent를 spawn할 때 task, cwd, scope, output contract를 모두 전달한다.

## 다른 플랫폼

native subagent 기능이 없으면 독립 CLI session이나 플랫폼의 team 기능을 사용할 수 있다. 다음 계약은 바꾸지 않는다.

- Lead가 유일한 orchestrator다.
- read-only와 write 작업을 구분한다.
- write Worker cwd는 전용 worktree다.
- 결과는 summary가 아니라 실제 diff/evidence로 review한다.

## Concurrency

- 가능한 동시 실행 수보다 task 독립성을 먼저 본다.
- slot이 부족하면 독립 lane을 순차 batch로 실행한다.
- reviewer는 구현 Worker와 분리한다.
- Worker에게 중첩 spawn을 허용하지 않는다.

## Approval boundary

승인 판단의 정본은 `dev-protocol`의 승인과 질문 및 §5.3이다. Worker 파일 생성만 승인받은 경우에는
commit/push·배포까지 확대하지 않는다. 반대로 사용자가 구체화된 `PR까지`, `개발서버 배포`, `운영까지`를
승인했다면 그 범위에 필요한 Worker commit, Lead 통합, push, merge, 비파괴적 migration을 단계마다
재확인하지 않는다. 실제 dry-run·검증과 프로젝트의 merge 담당자 규칙은 유지한다.
새 파괴적 변경, 미승인 운영 범위, 범위 밖 외부 write만 정확한 영향과 함께 추가 확인한다.
