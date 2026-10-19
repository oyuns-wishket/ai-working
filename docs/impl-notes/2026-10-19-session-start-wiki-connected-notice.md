# 2026-10-19 세션 시작 hook: 연결된 프로젝트의 wiki route 안내

## 목표 / 확정 사항

- 세션 시작 hook이 registry에 `connected`로 등록된 저장소에서 "[wiki 연결] <project> [connected] — 첫 비단순 작업 전에 `project-wiki-context route --query <과제>`…" 한 줄을 낸다. 미등록은 기존 `[wiki 미연결]`, `excluded`·`common-only`는 조용히 유지.
- 사용자 요청(2026-10-19, oyunseong-wiki 세션): "마지막에 어떤 프롬프트를 하든, 관련 프로젝트 찾아서 wiki 인식 최적화 하는것까지 ㄱㄱ". 프로젝트 인식 자체는 resolver가 이미 하고 있었으나, 연결된 프로젝트에서는 안내가 없어 route 단계가 자주 생략됐다.

## Gate evidence

- 사용자 요청·답변: 위 인용. 확인 질문 없음.
- 승인된 범위: `hooks/session-start.sh` 한 줄 추가, 테스트, 이 노트. 개인 동기화 저장소 규칙에 따라 main 직접 commit·push.
- 미승인 가정: wiki 본문·경로를 세션 컨텍스트에 주입하지 않는다(skill 규칙). namespace 경로도 출력하지 않는다(기존 테스트가 `sys-wiki` 문자열 노출을 금지).

## 계획 / 검증

- `doctor` JSON의 `mode=="wiki-bounded"`일 때만 출력. 테스트 `connected repositories name their namespace and the bounded route step; excluded ones stay silent` 추가. `node --test tests/hook-session-start.test.mjs` 20/20, `validate_skills.py`·`public_audit.py --history` 통과. 연결·신규 연결·제외 저장소 각 1개에서 hook 실측.

## 판단 근거

- 안내만 추가하고 route 자체를 hook에서 실행하지 않는 이유: route는 과제 질의가 필요하고 trace를 남기므로 세션 시작 시점에 돌리면 빈 질의·고아 trace가 생긴다.
- `[excluded]`에는 아무 말도 하지 않는다: 도구·자기 저장소에서 매 세션 소음이 되고, 안내할 행동이 없다.

## 개선 history

- 2026-10-07 `[wiki 미연결]` 안내 추가 → 2026-10-19 `[wiki 연결]` route 안내 추가. 다음 후보: 미마감 trace 안내에 trace가 속한 프로젝트 이름 노출(현재는 개수만).

## ⚠️ DEVIATION

- 없음
