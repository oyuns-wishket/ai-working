## 6. 운영배포 후 knowns wiki closeout

운영배포를 승인받아 검증까지 성공한 경우에만, HANDOFF 뒤 `knowns`를 정확히 한 번 실행한다. PR까지만 또는 개발서버까지만 진행했거나 운영배포가 실패·보류되면 wiki를 묻지 않는다. 문서 반영 후 task worktree 정리는 §5.4를 따른다.

1. 설치된 `knowns/SKILL.md`를 끝까지 읽고 적용한다. 없으면 `wiki closeout 미실행`을 blocker로 남긴다.
2. read-only 분석으로 후보, 연결, exact wiki write·검증·commit·push·배포 계획과 항목별 AI 추천을 만든다. `docs/handoff/HANDOFF.md`의 `## Wiki candidates` 적재분이 있으면 후보 입력에 포함한다.
3. 모든 미정 질문을 한 번에 묶어 `추천대로 / 수정사항 일괄 입력 / wiki 스킵`으로 묻는다.
4. `wiki 스킵`이면 `KNOWNS: skipped`로 전체 작업을 즉시 종료하고 다시 묻지 않는다.
5. `추천대로`면 모든 항목을 AI 추천안으로 확정한다. 수정 답변이면 한 번의 답에 포함된 값을 반영한다.
6. 이 한 번의 선택을 승인된 wiki 범위의 write·검증·commit·push·배포 승인으로 사용하고 추가 확인 없이 연속 실행한다.
7. 현재 completion chain에 `KNOWNS:` 결과가 있으면 재호출하지 않는다.

마지막 산출물은 `KNOWNS: ingested | no-op | skipped | blocked`다. wiki 관리 작업 자체는 `recursive-skip`한다.
