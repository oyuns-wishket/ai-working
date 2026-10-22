# 2026-10-22 요청별 wiki 맥락 hook

## 목표 / 확정 사항
- AI 작업 시 wiki 연결 프로젝트에서 사용자가 직접 `route`를 부르지 않아도 관련 wiki 문서를 매 요청마다 제시한다.
- 본문은 주입하지 않고 제목·종류·경로·섹션 범위만 넘긴다. 읽을지는 agent가 과제에 맞춰 판단한다.

## Gate evidence
- 사용자 요청·답변: "작업할때마다 맥락증강 잘되게 보완해줘".
- 확인 질문: 없음. 기존 retrieval 계약(route가 반환한 문서만 사용, raw·candidate 미열람, my-wiki 명시 binding만)을 그대로 따른다.
- 승인된 범위: ai-working hook·resolver 성능 개선·문서·테스트, PR·merge·로컬 bootstrap 설치.
- 미승인 가정: 없음.

## Issue tracking
- 대표: 생략 — 개인 SSOT 유지보수, 이 대화의 요청으로 추적.

## 측정한 문제
- retrieval feedback trace 27건 중 실제 사용 12건. 한 고객 ERP 저장소는 10-12 이후 실질 작업 세션 25개 중 `route` 호출이 1회였다.
  세션 시작 doctor만으로는 과제별 문서가 선택되지 않고, 수동 `route`는 잊히기 쉽다.
- `route` 1회가 약 3.4초로 prompt hook 제한 시간 안에 끝나지 않았다.

## 변경
- `hooks/prompt-wiki-context.mjs`: UserPromptSubmit에서 `route --record`를 4초 제한으로 호출하고, `wiki-bounded`일 때만 문서 4건 이하를 1800 bytes 이하로 주입한다. 세션별로 이미 제시한 문서는 생략한다.
- `wiki_context.py`: 후보 문서의 `source_refs` 검증에 쓰는 commit·blob 존재와 `HEAD` 대비 변경 여부를 `cat-file --batch-check` 한 번으로 미리 조회한다(`prefetch_source_objects`, `blob_ids`). 변경 판정은 `git diff --quiet` 대신 같은 경로의 blob id 비교다.
- `global/governance-hooks.json` 등록, `docs/hook-behavior.md`·README 표 갱신, `tests/hook-prompt-wiki-context.test.mjs` 추가.

## 검증
- `route` 실측 3.4초 → 0.8~1.0초. 질의 4개의 반환 문서·순서가 변경 전과 동일.
- 연결 저장소 실제 질의 2개: 관련 문서 4건과 trace id 반환. 같은 세션 재질의는 출력 없음, 짧은 질의·미연결 저장소는 출력 없음.
- `node --test tests/*.test.mjs`, resolver unittest, `validate_skills.py`, `public_audit.py --history`.

## 판단 근거
- 본문 주입 대신 경로만 넘긴다: context 비용을 고정하고, agent가 과제와 무관한 문서를 무시할 수 있다.
- 세션 dedup: 같은 주제의 후속 요청마다 같은 목록을 반복하면 잡음이 된다.
- 실패는 항상 무출력: hook이 작업을 막거나 오류 메시지로 context를 오염시키지 않는다.

## ⚠️ DEVIATION
- ⚠️ 처음에는 `source_refs` 경로별 `git diff --name-only`로 변경 여부를 모았으나 `route`가 5.5초로 느려졌다 → 대응: 되돌리고 blob id batch 비교로 교체 → 리뷰: 결과 동일성 실측 확인.
- ⚠️ 첫 prefetch는 route loop의 "regular file만" 검사보다 먼저 frontmatter를 열어, FIFO 문서가 있으면 resolver가 멈췄다(v2 test가 23분간 정지) → 대응: prefetch도 symlink·비정규 파일을 건너뛴다 → 리뷰: resolver 70 test 통과.

## 다음에 참고
- prompt hook 안에서 부르는 resolver는 Git 호출 수가 곧 지연이다. 문서 수에 비례하는 subprocess를 추가하지 않는다.
- feedback의 `used` 비율 변화로 효과를 다시 측정한다. 주입만으로 사용을 단정하지 않는다.
