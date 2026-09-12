# 2026-09-12 public-only AI SSOT

## 목표 / 확정 사항
- `oyuns-wishket/ai-working` public 저장소 하나만 Claude·Codex 규칙과 개인 제작 skill의 Git SSOT로 사용한다.
- `wishket-working`/`ai-working-private` 저장소와 local private overlay를 실행 경로에서 제거하고 퇴역시킨다.
- 지금까지 만든 reusable skill, hook, template, global rule의 최신 동작을 public 저장소로 이관한다.
- 앞으로 global `CLAUDE.md`/`AGENTS.md`, skill, bootstrap 관련 변경은 모두 `ai-working`에 쌓는다.
- secret 값, credential, 개인 네트워크 식별자, 고객 전용 상세는 public Git에 싣지 않는다. 재사용 가능한 절차는 placeholder·runtime discovery·project-local config 방식으로 보존한다.

## Gate evidence
- 사용자 요청: private 저장소를 쓰지 않고 모든 SSOT를 public `ai-working`으로 재연결하며, 서브에이전트를 활용한 Ralph loop로 9/10 이상까지 개선.
- 승인된 범위: public repo 파일 작성·검증·commit/push, 현재 Mac의 Claude/Codex/workspace/config 링크 전환, 기존 private repo 퇴역, 안전한 worktree 정리.
- 미승인/제외: credential/secret 공개, 고객 소유 비공개 자료 공개, 기존 dirty 변경 삭제, 제품 운영 배포.
- Tracking issue: https://github.com/oyuns-wishket/ai-working/issues/1
- 작업 진입: dev-protocol + agent-environment + personal-ai-ssot + multi-agent-dev. UI가 없어 design-workflow는 생략한다.

## 계획
1. 세 서브에이전트가 자산, runtime 연결, 공개 안전성을 독립 감사한다.
2. public-only 구조를 구현하고 최신 reusable 자산을 이관·일반화한다.
3. dry-run/apply/status/idempotency, skill validation, hook tests, secret/customer/path scan을 반복한다.
4. 아래 점수표를 독립 재감사해 9.0 미만 항목을 고친다.
5. public main에 반영한 뒤 현재 Mac 연결을 재적용하고 private 저장소를 퇴역시킨다.

## Ralph 점수표 (10점)
- 정본 단일화 2점: 활성 링크와 작성 규칙이 public `ai-working`만 가리킨다.
- 기능 이관 2점: reusable skills/hooks/templates/global rules의 최신 동작이 보존된다.
- 공개 안전성 2점: secret·개인 host/IP·고객 전용 상세와 private symlink가 0건이다.
- 설치 재현성 1.5점: 새 target에서 dry-run/apply/status/2차 apply가 통과한다.
- 운영 검증 1.5점: skill validator, scripts/tests, live link audit가 통과한다.
- 문서·미래 경로 1점: README와 authoring rules가 future writes를 public repo로 고정한다.

## 판단 근거
- private Git history 자체를 public으로 바꾸면 과거에 있던 개인·고객 정보까지 영구 공개되므로 fresh public history를 유지한다.
- 공개할 수 없는 값은 SSOT에서 제외하는 것이 아니라 public template과 machine/project-local configuration 경계로 바꾼다.
- 개인·고객 denylist 값은 public 코드에 난독화해 넣지 않고 machine-local 파일과 encrypted repository secret으로 공급한다.
- 최초 공개 과정의 임시 overlay commit도 reachable history에 남기지 않고 검토된 최종 snapshot을 새 public root로 게시한다.

## Ralph 개선 기록
- 1차 독립 감사: 저장소 산출물 9.4/10, 실제 환경 포함 6.9~8.4/10. live cutover, CI, history 검사, local config 이관이 blocker였다.
- 빈 사용자 홈의 `--dry-run`이 종료 코드 1을 내던 문제를 고치고 empty-home 회귀 테스트를 추가했다.
- public audit를 현재 tree뿐 아니라 모든 reachable commit의 path, mode, symlink, blob까지 fail-closed로 확장했다.
- 추가 token 형식과 개인 `.local` host 회귀 테스트를 넣고, MIT license와 26-skill catalog를 추가했다.
- `knowns` 실행 조건이 글로벌 규칙과 충돌하던 세 skill을 검증된 운영 배포 후로 한정했다.

## ⚠️ DEVIATION
- 이전 구현은 private overlay를 유지했으나 사용자의 명시적 정정과 맞지 않았다. 이번 작업에서 overlay를 제거하고 public-only로 교정한다.
