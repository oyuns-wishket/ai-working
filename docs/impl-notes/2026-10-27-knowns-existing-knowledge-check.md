# 2026-10-27 knowns 기존 지식 대조 단계 필수화

## 목표 / 확정 사항
- 개발 closeout으로 wiki에 넣는 지식이 기존 정본과 중복·모순되지 않게 한다.
- 이전 상태: `knowns` 3단계에 "기존 정본에 병합 가능한지 먼저 보고… 불명확하면 contested"라는 문장은 있었지만, helper(`inspect_context.py`)는 규칙 파일만 찾고 기존 note를 대조하지 않았다. 템플릿에도 대조 결과 칸이 없어 대조 여부가 결과에 남지 않았다. 같은 위키의 자동 ingest는 이미 코드로 `new/append/noop/hold` 판정을 강제하고 있어, 사람 경로가 더 느슨한 역전 상태였다.

## Gate evidence
- 사용자 요청: 개발 플로우의 wiki ingest 때 기존 wiki와 한 번 검토해 중복·모순이 생기지 않게 하자는 제안.
- 제안(위키 소유 대조 검사기 + knowns 필수 대조 표 + 위키 lint 중복 경고)에 대한 사용자 답: "오키 전체로 가자 ㄱㄱㄱ".
- 승인된 범위: `skills/knowns/` 문서·템플릿, 이 impl-note. 위키 저장소 변경은 위키 쪽 impl-note에 기록.
- 미승인 가정: 기존 wiki 문서의 병합·삭제는 하지 않는다.

## Issue tracking
- 대표: 생략 — 개인 SSOT 유지보수, 이 대화의 요청으로 추적.

## 변경
- `SKILL.md`: 3단계를 `3a 기존 지식 대조(필수)`와 `3b 추천 작성`으로 나눴다. 3a는 위키가 소유한 대조 검사기가 있으면 그것을, 없으면 같은 범위 note를 직접 읽어 같은 기준으로 판정한다. `contested`·오류·미판정은 `추천대로`로 덮지 않고 기존 유지·대체·범위 분리·contested 표시 중 추천 선택지를 단일 묶음에 둔다. ingest 단계는 판정을 따르게 했고(`noop`은 쓰지 않음, `append`는 지정 문서에만), 검증 게이트와 완료 보고에 `CHECK` 행을 추가했다.
- `assets/candidate-review.template.md`: "기존 지식 대조" 표와 "결정 필요" 표.
- `references/ingest-modes.md`: v2 계약 모드와 상태·충돌 처리에 3a 판정을 연결.

## 판단 근거
- 판정 엔진을 skill이 아니라 위키가 소유: 쓰기 범위·schema·자동 ingest와 같은 scope 규칙을 위키 코드가 이미 가지고 있다. skill에 복제하면 두 기준이 갈라진다. skill은 "검사기가 있으면 쓰고, 없으면 직접 같은 기준"만 정한다.
- 별도 승인 단계를 만들지 않음: contested 결정도 기존 단일 묶음 선택 안에 넣어 knowns의 "한 번만 묻는다" 계약을 유지했다.
- 대안 기각: skill 문장만 강화(모델 재량이라 재발), lint만 추가(들어간 뒤에야 발견, 그 사이 두 문서가 함께 주입됨).

## 검증
- `python3 scripts/validate_skills.py` → `skill validation passed: 25 skills`
- `python3 -m unittest discover -s skills/knowns/scripts -p "test_*.py"` → 26 tests OK
- 위키 검사기 실측(같은 날, 실제 위키 · 실제 모델): 기존 정본과 같은 의미의 후보 → `noop`, 기존 규칙을 뒤집는 가상 후보 → `contested`(충돌 문서 2건 지목), 무관한 가상 후보 → `new`. 약 30초.

## ⚠️ DEVIATION
- 없음

## 다음에 참고
- 위키 lint가 실측에서 기존 중복 의심 3쌍을 찾았다. 모두 자동 ingest가 "기존 문서와 범위가 다르다"며 `new`를 고른 것이다. 자동 ingest의 동의어 중복 방지도 완전하지 않으므로, 병합 여부는 위키 lint 보고로 사람이 결정한다.
