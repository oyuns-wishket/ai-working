# 2026-10-25 개발배포 직후 worktree·자원 자동 정리

## 목표 / 확정 사항
- 완료 절차 순서를 `개발배포 → 운영배포 → wiki → worktree 정리`에서 `개발배포 → 정리(자동) → 운영배포 → wiki`로 바꾼다.
- 정리는 개발배포 검증 직후 질문 없이 수행하고, 무엇을 정리·보존했는지만 보고한다.
- 운영배포와 wiki closeout은 정리가 끝난 뒤 진행한다.

## Gate evidence
- 사용자 요청(2026-10-25): "워크트리 정리하고 작업 전체 정리는 개발 배포하고 바로 진행해줘. 나머지 운영 배포와 위키 작성은 다 정리되고 해도 되잖아. 작업 정리는 개발배포하면 알아서 정리해주고 했다 알려주기만 하면 돼."
- 확인 질문: 없음
- 승인된 범위: `global/CLAUDE.md`, `skills/dev-protocol/SKILL.md`, `skills/dev-protocol/references/production-closeout.md`
- 미승인 가정: 없음

## Issue tracking
- 대표: 생략 (개인 SSOT 규칙 문구 변경, 단일 commit)

## 변경
- `global/CLAUDE.md` 승인·배포 절과 skill 표: 개발배포 검증 직후 worktree·자원 자동 정리, 그 뒤 운영·knowns.
- `skills/dev-protocol/SKILL.md`
  - 목적 5·6: 정리 시점을 개발배포 검증 직후로, 운영·wiki는 정리 뒤로 명시.
  - §5 도입부: "worktree 삭제는 closeout 뒤 마지막" 문장을 새 순서(§5.2→§5.3→개발배포→§5.5→§5.4→운영→§5.6·§5.7)로 교체.
  - §5.3: 옵션 2·3의 같은 턴 처리 순서를 HANDOFF→정리→(옵션 3) 운영배포→closeout으로 수정.
  - §5.4 제목·본문: "worktree·작업 자원 정리 (개발배포 직후, 자동)". 작업 자원(Docker/DB·dev server·임시 HTML 서버) 종료를 정리 대상에 포함하고 local-operations 종료 절차로 연결. 옵션 1·merge 전은 worktree 보존.
  - §5.6-3: 운영 후 HANDOFF 편집은 이미 정리된 상태이므로 primary checkout에서 반영.
- `references/production-closeout.md`: knowns 단계에서 worktree 정리를 다시 묻거나 미루지 않음.

## 판단 근거
- 운영배포 전에 정리하면 운영배포·knowns가 primary checkout에서 진행되고, 정리 대기 시간 동안 dev server·Docker가 메모리를 점유하는 문제(2026-10-19 dev server 메모리 가드)가 줄어든다.
- 기존 §5.4의 안전 조건(dirty·미병합·다른 세션 사용 보존, 강제 삭제 금지)은 그대로 유지했다. 바뀐 것은 시점과 "질문 없이 보고만"의 강조다.
- 옵션 1(PR까지)은 merge 전이므로 worktree를 보존하고 자원만 정리하도록 명시해, 정리 시점 전진이 미병합 작업 삭제로 이어지지 않게 했다.

## 기각안
- §5.4 번호를 §5.6 뒤로 재배치: 참조(§5.4)가 다른 문서·메모리에 있어 번호 유지, 순서는 §5 도입부에 명시.

## ⚠️ DEVIATION
- 없음

## 검증
- `python3 scripts/public_audit.py` 통과 여부는 commit 전 확인.
- 세 파일 grep으로 "closeout을 마친 뒤 마지막" 잔존 문구 없음 확인.

## 다음에 참고
- 완료 절차 번호(§5.4 등)는 외부 참조가 있어 본문 순서와 번호 순서가 다를 수 있다. 실제 순서는 §5 도입부 문장이 정본이다.
