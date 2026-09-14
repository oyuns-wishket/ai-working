---
name: multi-agent-dev
description: Coordinate independent implementation or investigation lanes with native Claude/Codex workers, isolated write worktrees, and independent review. Use for multi-agent requests or changes spanning modules, data, permissions, or integrations.
---

# multi-agent-dev — 적응형 ERP 멀티에이전트 개발

## Overview

현재 Git 프로젝트를 먼저 분석하고, 기존 Worker를 역량 기준으로 재사용하며, 부족한 Worker만 사용자 승인 후 Claude와 Codex용으로 영구 생성한다. Lead가 작업을 분해하고, 읽기 Worker는 공유 checkout에서, 쓰기 Worker는 각자 Git worktree에서 작업하게 한 뒤 결과를 직접 검토·통합·검증한다.

개인 절대경로를 Skill에 넣지 않는다. 최초 실행에서 필요한 경로를 한 번에 하나씩 질문하고 machine-local 설정에 저장한다.

## 고정값

| 항목 | 값 |
|---|---|
| 사용자 설정 | `~/.config/multi-agent-dev/config.json` 또는 `XDG_CONFIG_HOME` 아래 동등 경로 |
| 로컬 상태 | `~/.local/state/multi-agent-dev/` 또는 `XDG_STATE_HOME` 아래 동등 경로 |
| 프로젝트 Worker 정본 | `<repo>/.agents/multi-agent-dev/workers/*.json` |
| Claude adapter | `<repo>/.claude/agents/*.md` |
| Codex adapter | `<repo>/.codex/agents/*.toml` |
| 기본 Codex Worker effort | `high`; 고위험 리뷰·DB·보안은 필요 시 `xhigh` |
| Claude Worker effort | Worker가 명시적으로 override하지 않고 Lead 설정을 상속 |

세부 역할과 선택 조건은 [`references/worker-capabilities.md`](references/worker-capabilities.md), 플랫폼별 호출 규칙은 [`references/platform-adapters.md`](references/platform-adapters.md), 설정·Worker spec 형식은 [`references/schemas.md`](references/schemas.md)를 읽는다.

## 실행 여부 결정

다음 중 하나이면 이 Workflow를 실행한다.

- 사용자가 Skill이나 멀티에이전트/worktree 작업을 명시적으로 요청했다.
- 독립적인 조사·구현·테스트 lane이 둘 이상이다.
- ERP 업무 불변조건, DB/RLS/migration, 권한, 외부 연동, 데이터 대사 중 하나 이상이 중요하다.
- 변경 범위가 여러 모듈 또는 여러 앱에 걸친다.

단일 오타·문구·명백한 한 파일 수정은 Worker와 worktree 없이 Lead가 직접 처리하고, 생략 이유를 한 줄로 보고한다. 읽기만 하는 큰 분석은 병렬 Worker를 쓸 수 있지만 worktree는 만들지 않는다.

## 절차

### 0. 최초 설정

1. `python3 scripts/configure.py show --json`을 실행한다.
2. 설정이 없거나 필수 값이 유효하지 않으면 다음을 **한 번에 하나씩** 질문한다.
   - ERP/업무 프로젝트가 위치할 수 있는 workspace root. 여러 개 가능하며 optional이다.
   - 공유 ERP 도메인 문서 경로. 없으면 `없음`을 허용한다.
   - Worker worktree root.
   - 사용할 플랫폼: `claude`, `codex`, `both`.
3. 답을 받을 때마다 `configure.py set`으로 machine-local 설정에 저장한다.
4. `python3 scripts/configure.py validate --json`이 통과해야 다음 단계로 간다.

현재 Git root는 설정값으로 추측하지 말고 항상 `git rev-parse --show-toplevel`로 결정한다. 명시 요청 경로 → 프로젝트 설정 → 사용자 설정 → 자동 탐색 → 질문 순으로 값을 정한다.

### 1. 프로젝트와 기존 Worker 분석

1. 프로젝트의 `CLAUDE.md`, `AGENTS.md`, 필수 `.claude/rules/`, handoff, impl-note, 도메인 문서를 먼저 읽는다.
2. `project-wiki-context`로 Git remote identity를 resolve하고 이번 작업 문구로 route한다. 반환된 fresh canonical 문서만 프로젝트 문서 다음에 읽고, unresolved/stale/contested이면 repo-only로 계속한다.
3. 설정된 공유 ERP 문서가 있으면 프로젝트 문서 다음에 읽는다. 충돌하면 현재 프로젝트 문서·검증된 runtime이 우선이며 충돌을 보고한다.
4. `python3 scripts/inspect_project.py --project . --json`을 실행해 stack, package manager, 명령, DB, UI, 인증, 외부 연동, migration/data 신호와 기존 Worker를 수집한다.
5. 기존 `.claude/agents`, `.codex/agents`, 프로젝트 Worker 정본을 이름이 아니라 **역량·권한·지침** 기준으로 평가한다.
6. 기존 Worker가 충분하면 그대로 사용한다. 비슷하지만 부족하면 덮어쓰지 말고 수정 제안을 별도로 낸다.

### 2. 이번 작업의 Team 제안

Lead가 요구사항을 독립 lane으로 분해하고 다음 표를 먼저 사용자에게 보여준다.

| 역량 | 기존/신규 | 읽기/쓰기 | worktree | 담당 범위 | 선택 이유 |
|---|---|---|---|---|---|

다음 원칙을 지킨다.

- 역할 카탈로그 전체를 설치하지 않는다. 이번 작업과 프로젝트에서 필요한 최소 역량만 선택한다.
- 기존 `pm`, `developer`, `tester`, `reviewer`, `designer`와 전문 Worker를 우선 매칭한다.
- 구현 Worker끼리 파일 또는 모듈 소유권이 겹치지 않게 한다.
- 의존 관계가 있는 작업은 병렬처럼 위장하지 말고 순차 gate를 둔다.
- 모든 쓰기 결과는 독립 Reviewer와 Lead 검토를 거친다.

프로젝트 Worker를 새로 만들거나 기존 Worker를 수정해야 하면 이 표에서 정확한 파일과 이유를 밝히고 승인받는다.

### 3. 부족한 Worker 영구 생성

승인 후 Worker별 spec JSON을 `references/schemas.md`에 맞춰 임시 위치에 작성하고 다음을 실행한다.

```bash
python3 scripts/render_worker.py \
  --project <repo> \
  --spec <worker-spec.json> \
  --platform both
```

이 명령은 프로젝트 정본 spec과 Claude/Codex adapter를 함께 생성한다.

- 기존 파일이 있으면 기본 동작은 실패다. 자동 overwrite하지 않는다.
- 기존 Worker 수정은 변경 전후 diff를 다시 보여주고 별도 승인받은 뒤에만 `--force`를 쓴다.
- 생성 파일은 다음 세션에도 재사용하지만 commit하지는 않는다. commit/push는 사용자 승인을 따른다.
- 플랫폼 하나만 쓰는 사용자는 해당 adapter만 생성하되 정본 spec은 항상 남긴다.

### 4. 작업 분해와 worktree 배정

Lead가 각 task에 입력, 산출물, 파일 범위, 완료 조건, 검증 명령, 의존 task를 기록한다.

- 읽기 전용 Worker: Lead checkout 공유. 파일을 수정하거나 생성하지 않는다.
- 쓰기 Worker: Worker마다 별도 worktree와 branch를 만든다.
- Lead workspace가 dirty이면 worktree 생성을 중단하고 사용자 변경을 그대로 보존한다. 자동 stash, reset, checkout, force cleanup 금지.

쓰기 Worker worktree 생성:

```bash
python3 scripts/worktree_manager.py create \
  --repo <repo> \
  --session <task-slug> \
  --worker <worker-name> \
  --json
```

Worker에게 반환된 `worktree_path`를 명시하고 그 경로 밖의 파일을 수정하지 못하게 한다. Worker가 중첩 subagent를 다시 만들지 않게 한다.

승인받아 생성한 `.agents/multi-agent-dev/workers/`, `.claude/agents/`, `.codex/agents/` 파일만 dirty이고 다른 변경이 없다면 `--allow-generated-worker-metadata`를 추가할 수 있다. 생성 결과의 `excluded_dirty_worker_metadata`를 사용자에게 알린다. 그 외 dirty path가 하나라도 있으면 계속 중단한다.

### 5. Dispatch

예전 subagent-driven-development 요청도 이 절차로 수행한다. 작은 순차 작업에 Worker를 만들지 않고, 작업별 검토에서 요구사항 충족과 코드 품질을 함께 확인한다. 승인·완료 절차는 `dev-protocol` 한 곳에서 처리한다.

플랫폼의 native subagent 호출을 사용한다. Orchestration plugin은 필수 의존성이 아니다. 세부 매핑은 `references/platform-adapters.md`를 따른다.

각 Worker prompt에 반드시 포함한다.

- repo와 worktree 절대경로
- 담당 task와 수정 허용 범위
- 읽어야 할 프로젝트 규칙·ERP 문서
- Lead가 route한 task-relevant canonical wiki 문서 경로(없으면 `repo-only`)와 repo/runtime 우선순위
- 금지된 작업과 승인 gate
- 기대 산출물과 검증 명령
- 완료 시 반환할 summary 형식

Worker 반환 형식:

```text
STATUS: complete | blocked
SCOPE: 담당 범위
FILES: 변경/검토 파일
EVIDENCE: 실행한 검증과 결과
RISKS: 남은 위험
HANDOFF: Lead가 다음에 할 일
```

### 6. Lead review와 통합

Worker 완료를 그대로 성공으로 간주하지 않는다.

1. Lead가 각 worktree의 `git status`, diff, 변경 파일, 테스트 출력을 직접 확인한다.
2. 요구사항·ERP 불변조건·프로젝트 규칙·task 소유 범위를 대조한다.
3. 독립 Reviewer에게 raw diff와 수용 기준을 주고 PASS/FAIL을 받는다.
4. FAIL이면 해당 Worker만 최대 3회 재실행한다. 이후에도 실패하면 남은 위험과 선택지를 사용자에게 에스컬레이션한다.
5. Worker commit과 merge/cherry-pick은 현재 사용자 commit 승인 규칙을 따른다.
6. Lead 통합 workspace에서 프로젝트가 요구하는 lint, test, build와 DB/보안 gate를 실제 실행한다.
7. DB migration 적용, 외부 write, 배포, push의 승인 판단은 `dev-protocol`의 승인과 질문·§5.3을 따른다. 현재 요청이 이미 포함한 단계는 재질문하지 않고, 새 파괴적 변경·미승인 운영 범위·범위 밖 외부 write만 추가 확인한다.

### 7. 정리

통합과 검증이 끝난 뒤에만 실행한다.

```bash
python3 scripts/worktree_manager.py cleanup \
  --repo <repo> \
  --session <task-slug> \
  --target-ref <integrated-branch> \
  --json
```

cleanup은 clean이고 target에 통합된 worktree만 제거한다. dirty, 미통합, 경로 불일치 worktree는 보존하고 위치와 이유를 보고한다. 실제 worktree 폴더는 `git worktree remove` 성공 시 함께 제거된다.

### 8. 완료 인계

Lead는 Worker summary를 그대로 완료 근거로 쓰지 않고, 통합 workspace에서 확인한 diff·검증·결정·deviation만
최종 보고에 사용한다. 퀴즈나 별도 closeout 절차를 만들지 않는다. 간단 완료 보고, 조건부 배포 범위 선택,
worktree 정리, HANDOFF, 운영배포 후 `knowns`는 최신 `dev-protocol`의 완료 절차를 그대로 따른다.

## 안전 규칙

- 사용자 변경, 기존 Worker, 기존 branch를 자동 삭제·덮어쓰기·stash하지 않는다.
- 읽기 Worker에게 쓰기 권한을 주지 않는다.
- 같은 파일을 두 쓰기 Worker에게 동시에 배정하지 않는다.
- migration은 파일 작성과 실제 적용을 구분한다.
- ERP 수량·금액·상태 전이·권한·대사는 fail-closed로 검토한다.
- 프로젝트 규칙이 이 Skill보다 구체적이면 프로젝트 규칙을 우선한다.
- subagent 수보다 독립성과 검토 가능성을 우선한다.
- Worker가 registry를 무시하고 wiki/raw/observation 전체를 재귀 검색하지 못하게 한다.

## 검증 게이트

- 경로 설정과 Git root 검증 통과
- 기존 Worker 재사용/신규 생성 표에 사용자 승인 반영
- 쓰기 Worker별 독립 worktree와 파일 소유권 확인
- Lead와 독립 Reviewer의 결과 검토
- 프로젝트 lint/test/build 실제 결과 확보
- dirty 또는 미통합 worktree 보존
- 최종 보고에 생성 Worker, 통합 결과, 남은 worktree, 미해결 위험 포함
- 현재 배포 범위에 해당하는 `dev-protocol` 완료 절차 확인

## 트러블슈팅

| 증상 | 원인 | 대응 |
|---|---|---|
| 설정 경로가 다른 컴퓨터에서 깨짐 | 절대경로는 machine-local | `configure.py set`으로 해당 컴퓨터 값만 갱신 |
| 기존 Worker와 새 역할이 겹침 | 이름 기반 비교 | description·tools·instructions 역량을 비교하고 기존 Worker 우선 |
| worktree 생성 거부 | Lead workspace가 dirty | 사용자 변경을 보존하고 정리/commit 방향을 사용자에게 확인 |
| cleanup이 worktree를 보존 | dirty 또는 target에 미통합 | diff를 검토·통합한 뒤 cleanup 재실행 |
| Worker 결과가 충돌 | task/file ownership이 겹침 | Lead가 task를 다시 분해하고 순차 실행 |
| 특정 플랫폼 Worker를 못 찾음 | adapter 미생성 또는 세션 재시작 필요 | 정본 spec에서 adapter 생성 후 새 세션에서 재탐색 |
