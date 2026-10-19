# 2026-10-19 project-wiki-context: common-root topic sections

## 목표 / 확정 사항
- 지식 저장소의 AIDP 공통 루트(`sys-wiki/aidp`)가 자체 주제 섹션(FDE, 영업·제안, AX 사례, 운영·회계, 제품·설계, 공통 기술)을 선언할 수 있게 한다. 지금까지 공통 루트는 평면이었고 resolver는 `canonical_sections` 키로 `sys-wiki/aidp`를 예약어로 거부했다.
- 사용자 요청: "폴더 구조도 주제별로 확실히 알아보기 좋도록 … aidp내에서 일어나는 일은 aidp, personal 안에서도 주제별로 나누게".

## Gate evidence
- 사용자 요청·답변: 위 원문. 확인 질문 없음.
- 승인된 범위: resolver 스크립트·테스트, impl-note. 지식 저장소 측 contract·layout 변경은 그 저장소 history에 기록.
- 미승인 가정: 없음.

## 변경
- `skills/project-wiki-context/scripts/wiki_context.py` `knowledge_contract`: `sys-wiki/aidp` 자체는 섹션 네임스페이스로 허용. `sys-wiki/aidp/aidp`처럼 예약어 이름의 *프로젝트* 폴더는 계속 거부. 빈 parts 가드 추가.
- `scoped_directories`는 변경 없음: 선언된 섹션이 있으면 그 하위 폴더를 읽고, `common` 스코프에 기본 프로젝트 섹션을 추정하지 않는 기존 동작 유지.
- 테스트: 예약어 거부 케이스를 `sys-wiki/aidp/aidp`로 바꾸고, 공통 루트 섹션 문서가 common 스코프에서 served 되는 양성 테스트 추가.

## 판단 근거
- 보안 경계는 그대로다: 공통 루트 섹션은 contract가 선언한 폴더만 읽고, 고객 프로젝트 스코프는 영향 없다. `recursive: false`도 유지된다.
- 거부된 대안: 공통 지식을 별도 최상위 폴더(`sys-wiki/common`)로 옮기는 안. registry의 common read_scope 경로(`sys-wiki/aidp`)와 kb_check의 scope 규칙을 전부 바꿔야 해 범위가 커진다.

## 검증
- `python3 -m unittest discover -s skills/project-wiki-context/tests -p 'test_*.py'` → 70 tests OK.
- `python3 scripts/public_audit.py --history`, `python3 scripts/validate_skills.py` → 아래 결과 참조.

## ⚠️ DEVIATION
- 없음

## 다음에 참고
- 지식 저장소의 `knowledge_layout.namespace_for`도 같은 날 공통 루트 섹션을 프로젝트로 오인하지 않게 바뀌었다. 두 구현은 독립이라 한쪽만 바꾸면 route가 contract 오류로 fail-closed 된다.
