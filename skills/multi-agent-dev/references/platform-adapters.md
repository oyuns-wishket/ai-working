# Platform adapters

Skill의 역할 이름은 agent-neutral이다. 현재 플랫폼의 native mechanism으로 번역한다.

## Claude + OMC

- OMC 전역 역할이 프로젝트 역량을 충족하면 namespaced agent를 재사용한다.
  - 탐색: `oh-my-claudecode:explore`
  - 구현: `oh-my-claudecode:executor`
  - 리뷰: `oh-my-claudecode:code-reviewer`
  - 검증: `oh-my-claudecode:verifier`
  - DB/보안/테스트: 해당 OMC specialist
- 프로젝트 `.claude/agents/*.md`가 더 구체적이면 프로젝트 Worker를 우선한다.
- OMC `/team`이 프로젝트 Worker를 자동 치환한다고 가정하지 않는다. 필요한 agent name을 명시한다.
- Claude Worker에는 `effort` override를 생성하지 않아 Lead 설정을 상속시킨다.
- OMC native team worktree mode의 활성 여부를 추측하지 않는다. 이 Skill의 worktree manager가 경로를 만든 경우 Worker cwd를 명시적으로 그 경로로 고정한다.

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

Worker 생성 승인은 agent 파일 작성 승인이지 commit/push 승인이 아니다. 다음은 각각 별도 gate다.

- Worker branch commit
- Lead branch merge/cherry-pick
- DB migration apply
- 외부 시스템 write
- deployment
- push/PR merge
