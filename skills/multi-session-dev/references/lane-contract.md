# Lane contract — 호출자와의 단방향 계약

이 스킬은 호출자(보통 `dev-protocol`)의 절차를 참조하지 않는다. 아래 입력을 받고 아래 출력을 돌려주며, 입력에 없는 승인이 필요하면 `blocked`로 반환한다. 승인·이슈 종료·배포·HANDOFF는 호출자가 소유한다.

## 목차

1. 입력 계약
2. 출력 계약
3. lane 상태 전이
4. blocked 규칙

## 1. 입력 계약

Lead가 lane plan(`assets/lane-plan.schema.json`)을 만들기 전에 호출자로부터 확보해야 하는 값이다. 없으면 plan을 만들지 않고 호출자에게 되돌린다.

| 항목 | plan 필드 | 없을 때 |
|---|---|---|
| 승인된 write 범위(파일·모듈) | `lanes[].owned_paths` | write lane을 만들지 않는다 |
| commit 허용 여부 | `commit_allowed` | write lane 검증 실패. 호출자에게 commit 승인 필요를 알린다 |
| Lead task branch | `target_branch` | main/develop 직접 통합은 거부된다 |
| 수용 기준 | `lanes[].acceptance` | lane별 필수 |
| 검증 명령 | `lanes[].verify_commands`, 통합 시 `integrate.py --verify` | 없으면 "미실행"으로 보고 |
| 연결 이슈 | `issue` | `none` |
| 읽을 규칙 문서 | `rules_to_read` | repo의 `CLAUDE.md`/`AGENTS.md` |
| 허용 자원(DB·Docker·포트) | `resources` | 기존 자원만, 신규 기동 금지 |

push, PR, merge to develop/main, migration 적용, 외부 write, 배포는 입력 계약의 대상이 아니다. 이 스킬은 그 단계를 수행하지 않는다.

## 2. 출력 계약

Lead가 호출자에게 돌려주는 결과. `session_runner.py status --task <t> --json`과 `integrate.py` 출력을 근거로 작성한다.

```text
INTEGRATION: <target_branch>@<head_sha> | ok / conflicts / verify-failed / not-run
LANES:
  <id>  <status>  <platform>  attempts=<n>  branch=<b>  head=<sha>  verdict=<PASS|FAIL|N/A|->
  ...
EVIDENCE: 통합 workspace에서 실행한 검증 명령과 exit code
REVIEW: gate 리뷰 결과, advisory 리뷰의 주요 반론
WORKTREES: 정리된 lane / 보존된 lane과 이유(dirty, not-integrated, blocked, failed)
RISKS: lane이 보고한 위험 + Lead가 통합 중 발견한 위험
BLOCKED: 없음 / lane별 blocked_reason (호출자가 결정할 항목)
DEVIATION: 계획과 달라진 점
```

Worker summary를 그대로 완료 근거로 쓰지 않는다. `EVIDENCE`는 Lead가 통합 workspace에서 직접 실행한 결과만 넣는다.

## 3. lane 상태 전이

```text
planned → running → complete | blocked | failed | cancelled
                 ↘ skipped (의존 lane이 complete가 아님)
```

- `complete`: 결과 JSON이 스키마를 통과하고 `status=complete`, write lane은 uncommitted 변경이 없음.
- `blocked`: lane이 승인·입력 부족을 보고. worktree 보존.
- `failed`: 프로세스 비정상 종료, 결과 파싱 실패, 스키마 위반, uncommitted 변경, timeout. worktree 보존.
- `cancelled`: Lead가 중단. worktree 보존.
- `skipped`: runner가 의존성 미충족으로 시작하지 않음.

재시도는 `spawn --lane <id> --follow-up "<리뷰 피드백>"`(새 세션) 또는 `--resume`(같은 세션 이어가기)으로 하고 `retry_limit`을 넘기면 runner가 거부한다. 그 시점에 호출자에게 에스컬레이션한다.

## 4. blocked 규칙

다음은 lane이 스스로 판단하지 않고 `blocked`로 돌려보내야 하는 항목이다. 프롬프트 템플릿이 이를 명시한다.

- owned_paths 밖 파일 수정이 필요할 때
- migration 적용, 외부 서비스 write, push, 배포가 필요할 때
- 새 DB/Docker/서버 기동이 필요할 때
- 수용 기준이 서로 모순되거나 결정이 필요한 제품 선택이 남았을 때

Lead는 blocked 사유를 모아 출력 계약의 `BLOCKED`에 넣고 호출자에게 넘긴다. Lead가 사용자 승인을 대신 만들어내지 않는다.
