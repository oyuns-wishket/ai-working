# 2026-09-16 global 작업 방식 규칙 보강 (Workflow Orchestration)

## 목표 / 확정 사항
- 사용자가 제공한 Workflow Orchestration md(Plan Mode / Subagent / Self-Improvement / Verification / Elegance / Autonomous Bug Fixing / Task Management / Core Principles)를 `global/CLAUDE.md`에 기존 규칙과 중복 없이 통합한다. `~/.codex/AGENTS.md`는 bootstrap이 같은 파일을 동기화하므로 Claude·Codex 공통 적용.
- 파일 위치 매핑: `tasks/todo.md` → 이슈+HANDOFF(신설 안 함), `tasks/lessons.md` → wiki 연결 프로젝트는 sys-wiki `type: lesson`, 미연결은 프로젝트 HANDOFF `## Lessons`.

## Gate evidence
- 사용자 요청·답변: "아래 md 글 CLAUDE.md, AGENTS.md에 공통 적용" → 배치 선택지 제시 → "1 추천"(global ai-working).
- 확인 질문: 없음.
- 승인된 범위: 이 worktree의 `global/CLAUDE.md` 편집, validate/public_audit 실행, commit·push·PR(계획에 "PR → public-safety CI"로 명시하고 진행 승인 받음).
- 미승인 가정: 없음.

## Issue tracking
- 대표: 생략 — 규칙 문서 보강, ai-working open issue 0.
- 관련: oyuns-wishket/oyunseong-wiki#104 (lesson 저장 위치 규칙과 연동)
- 완료 시점: PR merge + public-safety CI + `bootstrap.sh --status`로 로컬 동기화 확인.

## 계획
1. 기존 global/CLAUDE.md 절과 대조해 새 절 "작업 방식 — 계획·검증·교훈" 작성(중복 항목은 보강 문구만).
2. `python3 scripts/validate_skills.py`, `python3 scripts/public_audit.py --history`, hook/bootstrap tests.
3. PR 생성 → CI → merge → `./bootstrap.sh --status`.

## 판단 근거
- 범용 엔지니어링 규칙이므로 wiki 전용 CLAUDE.md가 아니라 global SSOT에 둔다.
- `tasks/` 파일 신설은 global의 "work-log 디렉토리 선제 생성 금지"와 충돌 → 기존 이슈/HANDOFF/wiki 경로로 매핑.

## ⚠️ DEVIATION
- ⚠️ 범위 추가: `skills/project-wiki-context/scripts/wiki_context.py`의 type enum에 `lesson` 추가. oyunseong-wiki#104가 도입한 `type: lesson` 문서를 설치된 resolver가 거부하지 않도록 같은 PR에 포함 → 리뷰: 자체 확인(resolver 62 tests PASS, 연결된 고객 프로젝트의 실제 route에서 lesson 문서 top-1 회수).

## 검증 결과
- validate_skills 24 PASS, public_audit --history PASS, resolver 62 / knowns 26 / tests/*.py / multi-session-dev PASS, node --test 통과(요약은 PR 본문).

## 다음에 참고
- 없음
