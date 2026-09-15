---
name: multi-session-dev
description: Run independent implementation and review lanes as isolated Claude or Codex CLI sessions, one worktree per write lane, then integrate sequentially with conflict checks and cross-model review. Use for multi-lane or multi-module changes where file ownership can be split; skip sequential or same-file work.
---

# multi-session-dev — 세션 lane 오케스트레이션

## Overview

Lead 세션이 작업을 독립 lane으로 나누고, 읽기 전용 lane은 in-process subagent로, 쓰기 lane과 리뷰 lane은 별도 CLI 세션(`claude -p`, `codex exec`)으로 실행한다. 쓰기 lane마다 전용 worktree와 branch를 가진다. Lead가 lane branch를 자기 task branch에 순차 merge하고 통합 검증·리뷰를 거친 뒤 결과 계약을 호출자에게 돌려준다.

Lead가 Claude든 Codex든 같은 스크립트를 쓴다. 단, macOS에서 Codex Lead가 Codex lane을 띄우려면 Lead가 Full access로 실행되어야 한다. sandbox 안의 Codex Lead는 Claude lane만 쓸 수 있다. 조건과 증상은 `references/session-runners.md` §7에 있다. 승인·이슈·배포·HANDOFF는 이 스킬이 결정하지 않는다. 입력 계약에 없는 승인이 필요하면 `blocked`로 반환한다.

## 고정값

| 항목 | 값 |
|---|---|
| 사용자 설정 | `~/.config/multi-session-dev/config.json` (`XDG_CONFIG_HOME` 존중, 퇴역한 `multi-agent-dev` 설정을 읽기 fallback) |
| 로컬 상태 | `~/.local/state/multi-session-dev/` — `sessions/`(worktree manifest), `tasks/<repo-id>/<task>/`(lane 상태·프롬프트·로그) |
| lane branch | `msd/<task>/<lane>` |
| 프로젝트 Worker 정본 | `<repo>/.agents/multi-session-dev/workers/*.json` (adapter: `.claude/agents/*.md`, `.codex/agents/*.toml`) |
| 동시 세션 상한 | 기본 3 |
| 결과 스키마 | `assets/lane-result.schema.json` |

계약은 [`references/lane-contract.md`](references/lane-contract.md), 플랫폼별 명령·hook·로그는 [`references/session-runners.md`](references/session-runners.md), 모드 선택·wave·리뷰·통합·정리 규칙은 [`references/orchestration.md`](references/orchestration.md), Worker 역량은 [`references/worker-capabilities.md`](references/worker-capabilities.md), 설정·spec 형식은 [`references/schemas.md`](references/schemas.md)를 필요한 단계에서만 읽는다.

## 실행 여부

다음 중 하나이면 실행한다.

- 파일 소유권이 겹치지 않는 쓰기 lane이 둘 이상이다.
- 구현과 다른 플랫폼·세션의 독립 리뷰가 필요하다.
- 사용자가 멀티세션·멀티에이전트·worktree 병렬 작업을 명시했다.

단일 파일 수정, 순차 의존이 강한 작업, 같은 파일을 여러 lane이 건드리는 작업은 Lead가 직접 처리하고 생략 이유를 한 줄로 남긴다. 세션 lane은 규칙·hook·skill을 다시 로드하므로 단일 세션보다 토큰이 수 배 든다.

## 절차

### 0. 설정과 프로젝트 분석

1. `python3 scripts/configure.py show --json` → 없거나 무효하면 `set`으로 worktree root, 플랫폼, `--max-parallel`, `--role-default`를 한 번에 하나씩 채운다. `validate --json` 통과가 조건이다.
2. 프로젝트 `CLAUDE.md`, `AGENTS.md`, `.claude/rules/`, 필요한 HANDOFF 절만 읽는다. `project-wiki-context`가 연결되어 있으면 이번 작업 문구로 route한 fresh 문서만 추가한다.
3. `python3 scripts/inspect_project.py --project . --json`으로 stack·명령·DB·UI·연동 신호와 기존 Worker를 수집한다. 기존 Worker는 이름이 아니라 역량·권한·지침으로 평가한다.
4. 부족한 Worker는 표에서 승인받은 뒤 `render_worker.py --spec <json> --platform both`로 만든다. 기존 파일은 덮어쓰지 않는다.

### 1. 입력 계약 확인

호출자로부터 승인된 write 범위, commit 허용 여부, Lead task branch, 수용 기준, 검증 명령, 연결 이슈, 허용 자원을 확보한다. 하나라도 없으면 plan을 만들지 않고 `lane-contract.md` §1의 표대로 무엇이 빠졌는지 호출자에게 돌려준다.

### 2. lane 계획

`assets/lane-plan.example.json`을 본떠 plan JSON을 작성하고 검증한다.

```bash
python3 scripts/lane_plan.py validate --plan <plan.json> --json
```

세션을 띄우기 전에 다음 표를 사용자에게 보여준다. 표의 범위가 입력 계약으로 이미 승인된 범위 안이면 답을 기다리지 않고 바로 실행한다. 승인 범위 밖의 쓰기 경로, 새 Worker 파일 생성, 입력 계약에 없는 commit·자원 사용이 표에 들어갈 때만 그 차이를 확인한다.

| lane | 모드 | 플랫폼/모델 | 읽기/쓰기 | 소유 경로 | 의존 | 수용 기준 |
|---|---|---|---|---|---|---|

- 쓰기 lane은 항상 `session` + 전용 worktree. 소유 경로가 겹치면 검증이 실패하므로 lane을 다시 자른다.
- 읽기 전용 조사는 `subagent`. 리뷰는 `session` read-only이며 gate는 Claude, advisory는 Codex를 기본으로 한다.
- Lead workspace가 dirty이면 worktree 생성이 거부된다. 사용자 변경을 보존하고 commit 방향을 확인한다. 자동 stash·reset 금지.

### 3. 실행

```bash
python3 scripts/session_runner.py run --plan <plan.json> --wave 0 --json
python3 scripts/session_runner.py run --plan <plan.json> --wave 1 --json
```

- `run`은 slot과 의존성을 지키며 spawn하고 종료까지 기다린 뒤 결과를 수집한다. 진행 중에는 다른 셸에서 `status --task <t>`로 표를 본다.
- subagent lane은 runner가 실행하지 않는다. Lead가 플랫폼 native subagent로 같은 프롬프트 계약을 주고 결과를 plan 표에 기록한다.
- lane이 `blocked`/`failed`이면 `attempt-N/stderr.log`, `permission_denials`, `result_problems`를 본 뒤 `spawn --lane <id> --follow-up "<지시>"` 또는 `--resume`으로 재시도한다. `retry_limit`을 넘기면 runner가 거부하며 그때 에스컬레이션한다.
- 한 lane의 결과 summary를 다른 lane의 근거로 넘길 때는 diff·검증 출력 같은 실제 산출물을 넘긴다.

### 4. 통합과 리뷰

```bash
python3 scripts/integrate.py --task <t> --dry-run
python3 scripts/integrate.py --task <t> --verify "<lint>" --verify "<test>" --verify "<build>"
```

1. Lead task branch를 checkout한 clean 통합 workspace에서 실행한다.
2. lane은 plan 순서대로 하나씩 merge된다. `merge-tree` 충돌 lane은 merge하지 않고 파일 목록만 보고한다. Lead가 직접 해결하거나 해당 lane을 rebase 지시와 함께 재실행한다.
3. 검증 명령은 통합 workspace에서 실행되고 로그가 state에 남는다. Lead는 `git diff <target>...HEAD`를 직접 읽고 수용 기준과 대조한다.
4. 리뷰 lane(read-only 세션)에 통합 branch와 수용 기준을 주고 `run`으로 실행한다. gate FAIL은 통합 완료를 막는다. advisory FAIL은 `RISKS`로 넘긴다.

### 5. 정리와 반환

통합·검증·리뷰가 끝난 뒤에만 실행한다.

```bash
python3 scripts/worktree_manager.py cleanup --repo <repo> --session <task> --target-ref <target_branch> --json
```

clean이고 target에 포함된 worktree만 제거한다. dirty·미통합·blocked·failed lane의 worktree는 보존하고 이유를 보고한다. 그런 다음 `lane-contract.md` §2 형식으로 호출자에게 반환한다. Worker summary가 아니라 통합 workspace에서 확인한 diff·검증·리뷰만 근거로 쓴다. push·PR·배포·이슈 종료·HANDOFF는 호출자가 이어서 처리한다.

## 안전 규칙

- 사용자 변경, 기존 Worker, 기존 branch를 자동 삭제·덮어쓰기·stash하지 않는다.
- 쓰기 권한은 세션 lane에만, 그것도 `owned_paths` 안에서만 준다. subagent에게 쓰기를 주지 않는다.
- lane은 push, merge, 배포, migration 적용, 외부 write, 새 DB/Docker 기동을 하지 않는다. 필요하면 `blocked`.
- lane은 다른 세션·team·background agent를 만들지 않는다. runner가 환경변수로 중첩 spawn을 거부한다.
- Codex 쓰기 lane은 `workspace-write` sandbox, 읽기 lane은 `read-only`. bypass 옵션은 쓰지 않는다. Claude lane은 도구 deny 목록으로 push·commit(읽기 lane)을 막는다.
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`는 lane에서 `0`이다. agent teams와 이 runner를 함께 쓰지 않는다.
- 리뷰어는 리뷰 대상을 수정하지 않는다. 구현 세션과 리뷰 세션을 분리한다.
- ERP 수량·금액·상태 전이·권한·대사는 fail-closed로 검토한다. 프로젝트 규칙이 더 구체적이면 프로젝트 규칙이 우선한다.

## 검증 게이트

- 설정 유효, Git root 확정, 입력 계약 완비
- `lane_plan.py validate` 통과와 사용자에게 보인 lane 표
- 쓰기 lane마다 독립 worktree·branch, Lead checkout 무변경
- lane 결과가 스키마를 통과하고 write lane worktree가 clean
- `integrate.py` 충돌 0, 검증 명령 exit 0, gate 리뷰 PASS
- cleanup 결과와 보존된 worktree 이유
- 반환 계약에 통합 sha, lane별 증거, BLOCKED, RISKS, DEVIATION 포함

## 트러블슈팅

| 증상 | 원인 | 대응 |
|---|---|---|
| `nested spawn refused` | lane 세션 안에서 runner를 호출 | Lead에서만 호출한다 |
| `max_parallel reached` | slot 소진 | `wait` 후 spawn하거나 `run`을 쓴다 |
| lane이 즉시 `failed`, `permission_denials` 비어있지 않음 | `--permission-prompts none`이 prompt를 거부 | 필요한 도구를 plan `disallowed_tools`에서 빼거나 lane 범위를 줄인다 |
| Codex `invalid_json_schema` | 스키마에 `additionalProperties:false` 누락 | `assets/lane-result.schema.json`을 수정 없이 사용한다 |
| write lane `complete`인데 `failed`로 표시 | uncommitted 변경 | `--follow-up "commit your work"`로 재시도 |
| `integrate.py`가 `expected target` 거부 | 통합 workspace가 다른 branch | Lead task branch를 checkout한다 |
| conflicted lane | 소유권 밖 파일 수정 또는 공유 파일 | 파일 목록 확인 후 Lead가 해결하거나 rebase 재실행 |
| 이전 task의 worktree가 남음 | Lead 비정상 종료 | `session_runner.py status`로 확인, 검토 후 cleanup |
| `claude`/`codex` not found | PATH 또는 alias 문제 | `configure.py set --binary claude=<path>` |
| worktree 생성 시 `cannot lock ref ... .git/refs` | sandbox 안의 Codex Lead가 `.git` 쓰기 불가 | Lead를 Full access로 실행하거나 Claude Lead 사용. `session-runners.md` §7 |
| Codex lane `failed to initialize in-process app-server client` | sandbox 안의 Codex Lead가 `~/.codex` 쓰기 불가 | 같은 대응 |
| Codex lane `blocked`, `sandbox_apply: Operation not permitted` | sandbox 안의 Lead가 Codex lane을 띄워 중첩 sandbox 발생 | Lead를 Full access로 실행. lane sandbox는 끄지 않는다 |
