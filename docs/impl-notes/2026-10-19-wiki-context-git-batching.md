# 2026-10-19 project-wiki-context: Git 조회 batching으로 세션 시작 hook 안에 들어오게

## 목표 / 확정 사항
- 사용자 확인 질문("AI 작업시 wiki 맥락 증강까지 된 거지?")에 실측으로 답하다 발견: 연결 프로젝트(380 노트)에서 `doctor`가 5.0초 걸려 session-start hook의 3초 guard(`run_guarded 3`)에 잘렸고, 그 결과 `[wiki 연결]` 안내가 세션 시작 시 조용히 빠지고 있었다. 자동화·resolver는 정상인데 사람이 보는 첫 안내만 빠진 상태.

## Gate evidence
- 사용자 요청: 위 확인 질문. 수정은 성능 결함 교정이라 별도 확인 질문 없음.
- 승인된 범위: resolver 스크립트, 테스트, impl-note.

## 원인
- `source_reference_health`가 정본 1건의 `source_refs`마다 `git cat-file -e`·`merge-base --is-ancestor`·(경로)`cat-file -e`를 각각 프로세스로 띄웠다. 488 노트 → 431 git 프로세스 → 4.8초(프로파일).

## 변경
- `git_objects_exist`: 프로세스당 캐시 + `cat-file --batch-check` 한 번으로 commit·경로 존재 확인.
- `head_ancestors`: `rev-list HEAD` 한 번으로 조상 집합을 만들어 `merge-base --is-ancestor`를 set lookup으로 대체. 약어 sha는 `git_objects_full`로 전체 id로 정규화.
- 의미 변화 없음: 같은 참조에 같은 판정. `changed_since`(diff)는 그대로 프로세스 호출.

## 검증
- 가장 큰 고객 프로젝트(380 노트) `doctor` 5.0s → 2.2s, 두 번째 고객 프로젝트 1.7s, `route` 1.9s. session-start hook에서 `[wiki 연결]` 3/3 출력(이전 0/3).
- resolver 70 tests OK, `hook-session-start.test.mjs` 21 pass.

## 다음에 참고
- hook guard(3초)는 fail-open이라 느려지면 **안내만 조용히 사라진다**. 연결 프로젝트가 커지면 `doctor` 시간을 주기적으로 재측정한다.
- 남은 비용은 `diff --quiet`(참조 경로 변경 여부)와 Python 자체 파싱이다. 더 줄이려면 `diff`도 `--name-only sha..HEAD` 한 번으로 묶을 수 있다.
