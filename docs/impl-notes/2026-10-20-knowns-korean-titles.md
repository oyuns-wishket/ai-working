# 2026-10-20 knowns: 새 정본 제목은 한국어 + 핵심 주제

## 목표 / 확정 사항
- 사용자 보고: 다른 세션에서 wiki 문서를 만들게 하면 영어 제목으로 생성된다. 2026-10-19 결정("제목은 한글 + 핵심 주제")이 skill 본문에 없어 세션마다 모델 재량이었다.

## Gate evidence
- 사용자 요청: "wiki 문서 만들라는 스킬에도 한글로 핵심을 제목으로 만들어주는지 확인해줘". 확인 질문 없음.
- 승인된 범위: knowns SKILL.md·리뷰 템플릿 문구, impl-note.

## 변경
- `skills/knowns/SKILL.md` 3절 규칙에 제목 규칙 한 줄(예시 포함, 식별자 유지, 본문 H1 동일, 위키 validator가 거부함을 명시).
- `assets/candidate-review.template.md` "넣을 후보" 머리에 같은 규칙.
- 지식 저장소 쪽(같은 날): canonical validator가 한글 없는 `title`을 오류로 내고 kb_check가 막는다. 그래서 skill이 규칙을 잊어도 commit 전에 걸린다.

## 판단 근거
- 규칙을 skill 본문에 두면 세션 간 일관성이 생기지만 보장은 아니다. 보장은 저장소 validator가 한다(이중 안전).

## 검증
- `validate_skills.py` 24 OK. 저장소: 기존 영어 제목 3건 교정 후 kb_check 0 errors, unittest 통과(fixture 제목 한글화).

## ⚠️ DEVIATION
- 없음
