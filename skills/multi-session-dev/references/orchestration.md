# Orchestration — 모드 선택, wave 실행, 리뷰, 통합

## 목차

1. 실행 여부와 모드 선택
2. lane 분해 규칙
3. 모델 라우팅 기본값
4. wave 실행
5. 리뷰 정책
6. 통합과 충돌
7. 재시도와 에스컬레이션
8. 정리 시점
9. 근거

## 1. 실행 여부와 모드 선택

세션 lane은 규칙·hook·skill을 다시 로드하므로 단일 세션보다 토큰이 수 배 든다. 다음 중 하나가 아니면 이 스킬을 쓰지 않고 Lead가 직접 처리한다.

- 파일 소유권이 겹치지 않는 쓰기 lane이 둘 이상이다.
- 다른 플랫폼의 독립 리뷰가 필요하다.
- 읽기 전용 조사가 여러 방향으로 갈리고 한 컨텍스트에 안 들어간다.

| lane 성격 | 모드 |
|---|---|
| 읽기 전용 조사·지도화·검증 재측정 | `subagent` |
| 쓰기 구현·테스트 작성 | `session` + worktree (예외 없음) |
| gate 리뷰 | `session`, read-only |
| advisory 리뷰(반론) | `session`, read-only, `advisory: true` |
| 특정 모델·effort 지정이 필요한 lane | `session` |

순차 의존이 많거나 같은 파일을 여러 lane이 건드려야 하면 lane을 합치거나 단일 세션으로 돌아간다.

## 2. lane 분해 규칙

- write lane마다 `owned_paths`를 명시한다. 두 write lane의 소유 경로가 겹치면 `lane_plan.py`가 실패한다. 경고가 아니다.
- 공유 파일(설정, 스키마, fixture, 라우트 테이블)은 한 lane에 몰거나 Lead가 통합 후 직접 수정한다.
- 의존 관계는 `depends_on`으로 적는다. 병렬처럼 위장하지 않는다.
- lane당 산출물은 함수·파일·테스트·리뷰처럼 자체 완결 단위로 한다. 5~6개 이상의 작업을 한 lane에 넣지 않는다.
- 세션 lane 수는 기본 3, 최대 5를 넘기지 않는다. 넘으면 wave를 나눈다.

## 3. 모델 라우팅 기본값

machine-local config `role_defaults`로 역할별 기본을 두고, plan에서 lane 단위로 override한다.

| 역할 | 권장 기본 | 비고 |
|---|---|---|
| implementation-worker | `claude` (Lead 모델 상속) 또는 `codex` high | 모듈 성격과 계정 여유로 결정 |
| test-engineer | 구현자와 다른 세션 | 같은 플랫폼이어도 됨 |
| reviewer (gate) | `claude` | §5 근거. 구현 세션과 분리 |
| reviewer (advisory) | `codex` high/xhigh | 비차단 반론 |
| db-guardian, security-auditor | `xhigh` 또는 Lead 상위 모델 | 고위험 |

설정 예:

```bash
python3 scripts/configure.py set \
  --role-default 'reviewer:claude_model=opus' \
  --role-default '*:codex_effort=high' \
  --max-parallel 3
```

## 4. wave 실행

`lane_plan.py validate --json`이 의존성 기준 wave를 계산한다. Lead는 wave 순서대로 실행한다.

```bash
python3 scripts/session_runner.py run --plan plan.json --wave 0 --json
python3 scripts/session_runner.py run --plan plan.json --wave 1 --json
```

- `run`은 slot(`max_parallel`)을 지키며 spawn하고, 의존 lane이 `complete`가 아니면 해당 lane을 `skipped`로 표시한다.
- `run`은 blocking이다. 실행 중 상태는 다른 셸에서 `status --task <t>`로 본다.
- wave 사이에 Lead가 개입할 필요가 없으면 `run --plan plan.json`(전체)으로 한 번에 돌릴 수 있다.
- write lane이 `complete`로 끝나면 lane branch에 commit이 있고 worktree는 clean이다. 그렇지 않으면 runner가 `failed`로 바꾼다.

## 5. 리뷰 정책

- gate 리뷰어는 구현 세션과 다른 세션이며 read-only다. raw diff와 수용 기준을 받고 PASS/FAIL을 돌려준다. 리뷰어는 리뷰 대상을 수정하지 않는다.
- gate 리뷰의 FAIL은 통합을 막는다. advisory 리뷰의 FAIL은 막지 않고 `RISKS`에 반영한다.
- gate 리뷰어 기본 플랫폼은 Claude다. Codex는 advisory로 붙인다. 근거는 §9.
- 리뷰 lane은 보통 통합 후 통합 branch를 대상으로 한 번 돌린다. lane별 리뷰는 lane이 크거나 위험할 때만 추가한다.

## 6. 통합과 충돌

```bash
python3 scripts/integrate.py --task <t> --dry-run              # merge-tree 충돌 검사만
python3 scripts/integrate.py --task <t> --verify "pnpm lint" --verify "pnpm test"
```

- 통합 workspace는 Lead task branch를 checkout한 clean 상태여야 한다. 아니면 거부한다.
- lane은 plan 순서대로 하나씩 merge한다(`--no-ff`). merge 전에 `git merge-tree --write-tree`로 충돌을 확인하고, 충돌 lane은 merge하지 않고 파일 목록을 보고한다. 자동 해결하지 않는다.
- 충돌 처리 선택지: Lead가 통합 workspace에서 직접 해결, 또는 충돌 lane을 `--follow-up "rebase onto <target>@<sha> and resolve <files>"`로 재실행.
- 통합 후 검증 명령은 통합 workspace에서 Lead 권한으로 실행되며 로그는 state 디렉토리에 남는다. 충돌이 하나라도 있으면 검증은 실행하지 않는다.

## 7. 재시도와 에스컬레이션

- 리뷰 FAIL·failed·blocked lane은 원인을 확인한 뒤 `spawn --lane <id> --follow-up "<구체적 지시>"`로 재시도한다. 같은 대화를 이어가야 하면 `--resume`.
- `retry_limit`(기본 3)을 넘기면 runner가 거부한다. 그때 lane의 diff·로그·blocked 사유를 모아 호출자에게 에스컬레이션한다.
- 재시도해도 같은 실패가 반복되면 lane 분해가 잘못된 것이다. 재시도 대신 plan을 다시 짠다.

## 8. 정리 시점

- 세션 종료 시: 프로세스만 정리된다. worktree·branch·로그는 남는다.
- 통합·검증·리뷰 완료 시: `worktree_manager.py cleanup --session <task> --target-ref <target_branch>`로 clean이고 target에 포함된 worktree만 제거한다. dirty·미통합·blocked·failed lane의 worktree는 보존하고 이유를 출력 계약의 `WORKTREES`에 적는다.
- Lead가 비정상 종료한 경우: 다음 실행에서 `session_runner.py status`(task 미지정)가 repo의 남은 task와 worktree를 나열한다. 자동 삭제하지 않는다.
- state 디렉토리(`tasks/<repo-id>/<task>/`)는 감사용으로 남긴다. 용량이 문제면 사용자에게 알리고 지운다.

## 9. 근거

- 33,596 agent PR 분석: 교차 에이전트 conflict 41.7%, 단일 에이전트 19.8%, 파일 집합이 겹치지 않으면 0에 근접. 순차 merge + rebase 권장. → §2 소유권 실패 처리, §6 순차 merge.
- Anthropic multi-agent research 포스트: 멀티에이전트 토큰 약 15배, 코딩은 research보다 병렬화 여지가 적음. → §1 실행 여부 판단.
- Cross-model review 논문(arXiv 2607.21656, LeetCode 116문제, 실행 없는 리뷰): Claude가 Codex 초안 리뷰 시 71.6→89.7%, Codex가 Claude 초안 리뷰 시 91.4→82.8%. 실제 repo 일반화는 검증되지 않음. → §5 gate=Claude, Codex=advisory. 실무에서 advisory 반론의 적중률을 관찰한 뒤 재평가한다.
- Claude Code agent teams 문서: 실험적, Claude 전용, `-p`에서 teammate 미생성, teammate별 worktree 없음. → 대체재로 채택하지 않음.
- 실무 보고 다수: 3~5 lane 이상은 사람 리뷰가 병목. worktree는 DB·포트·credential을 격리하지 않음. → §2 상한, 프롬프트의 자원 제한.
