# 2026-10-12 ai-working 작업 이력 기록 규칙

## 목표 / 확정 사항
- ai-working에서 작업하면 작업 이력을 남기도록 저장소 규칙(`AGENTS.md`, `CLAUDE.md`는 `@AGENTS.md`)을 영어로 갱신한다.
- 목적: 다음 개선 때나 다른 모델로 같은 변경을 다시 검증할 수 있게 한다.

## Gate evidence
- 사용자 요청: "ssot 작업 폴더 AGENTS.md에 작업하면 작업 history남기라고 영어로 최신화 해줘".
- 승인 범위: `AGENTS.md` 갱신, 이 노트 추가, commit·push(이 저장소의 main 직접 반영은 전역 규칙의 개인 동기화 저장소 예외).

## 변경
- `AGENTS.md`에 규칙 추가:
  - 모든 변경은 같은 commit/PR에 `docs/impl-notes/YYYY-MM-DD-<topic>.md`를 남긴다(목표·결정, 요청·승인, 변경, 근거·기각안, 이탈, 검증 명령과 결과, 후속 과제).
  - 여러 단계로 이어지는 개선은 기존 누적 이력 문서(예: `docs/rule-unification-history.md`)의 불변식·단계·검증 절을 갱신한다.
  - 새 이력 문서는 README에서 링크하고, 공개 안전 규칙(고객 프로젝트는 역할로만 기술)을 따른다.

## 판단 근거
- 기존 관행(`docs/impl-notes/` 날짜별 노트 18개, 누적 이력 문서 1개)을 규칙으로 고정했다. 새 디렉터리나 형식을 만들지 않았다.
- 절 구성은 최근 노트의 형식(목표·Gate evidence·계획·판단 근거·DEVIATION·검증)과 맞췄다.

## 검증
- `python3 scripts/public_audit.py --history`, `python3 scripts/validate_skills.py` 통과 후 push, `public-safety` CI 확인.
