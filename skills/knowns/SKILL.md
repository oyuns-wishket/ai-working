---
name: knowns
description: Use only after a verified production deployment to close out meaningful product development by analyzing verified artifacts, presenting one batched wiki decision with AI recommendations, honoring an immediate wiki skip, and then ingesting, validating, committing, pushing, and deploying the selected knowledge without additional confirmation. Triggers on "knowns", "위키에 저장", "지식 반영", "추천대로 정리", "wiki closeout", or when dev-protocol finishes a successful production deployment. Skip pre-production, pure lookup/no-delta, and recursive wiki-management runs.
---

# knowns — 운영배포 후 한 번에 끝내는 wiki closeout

## 목적

운영배포로 검증된 작업의 의미·목표·기여를 연결된 wiki에 남긴다. 사용자에게 여러 차례 묻지 말고, 모든 후보와 AI 추천 및 exact publish plan을 한 묶음으로 보여준 뒤 선택 한 번으로 write·검증·commit·push·배포까지 끝낸다.

## 절대 게이트

1. **운영배포 뒤에만 묻는다.** 현재 작업의 운영배포 성공 증거가 없으면 wiki 질문을 하지 않고 `not-after-production`으로 종료한다.
2. **사용자 선택은 한 번 받는다.** 후보, 추천, 의미·목표·기여·성공 상태, 연결, 파일, 검증, Git, 배포 계획을 한 번에 보여준다.
3. **선택 의미를 고정한다.**
   - `추천대로`: 모든 값을 AI 추천안으로 확정하고 전체 wiki pipeline을 승인한다.
   - `수정: ...`: 적은 항목만 바꾸고 나머지는 추천안으로 확정하며 전체 wiki pipeline을 승인한다.
   - `wiki 스킵`: 아무것도 쓰지 않고 `KNOWNS: skipped`로 전체 작업을 종료한다.
4. **추가 승인을 묻지 않는다.** 스킵이 아닌 한 번의 답은 표시한 wiki 범위의 write·검증·non-force commit·push·배포 승인이다.
5. **wiki 자체 규칙을 우선한다.** 규칙 충돌, 권한 불명, 승인 범위 밖 변경이 생기면 확장하지 말고 `blocked`로 보고한다.
6. **프로젝트 저장소를 건드리지 않는다.** wiki와 별도인 프로젝트 code repo, unrelated dirty/staged 파일, 기존 local-only commit은 자동 반영하지 않는다.
7. **파괴적 Git 동작을 금지한다.** force push·amend·rebase·reset·자동 pull을 하지 않는다.
8. **재귀 호출을 막는다.** `knowns` 자체, wiki ingest/curation, 이미 진행 중인 closeout은 `recursive-skip`한다.

## 입력

- 실제 project root와 원본 project identity
- 사용자 요청, issue/spec, 구현노트, deviation
- Git diff와 변경 파일
- lint, test, build, E2E, 운영배포 증거
- HANDOFF와 남은 blocker
- HANDOFF `## Wiki candidates` — 개발 배포 클로즈아웃(dev-protocol §5.6)이 적재한 후보 델타. 있으면 승격 후보로 단일 묶음에 포함한다(반영 후 HANDOFF 정리는 dev-protocol 책임).
- 현재 대화에서 사용자가 이미 설명한 의미·목표·기여

없는 값은 추측하지 말고 AI 추천으로 명시한다.

## 절차

### 0. 실행 여부 판정

- 운영배포 성공 증거가 없으면 질문 없이 `not-after-production`으로 종료한다.
- durable delta가 없으면 `no-durable-delta`로 종료한다.
- 재귀 방지 대상이면 `recursive-skip`으로 종료한다.
- 그 외에만 아래 절차를 실행한다.

### 1. 연결된 wiki 탐색 — read-only

1. `git rev-parse --show-toplevel`로 project root를 확인한다.
2. project의 `AGENTS.md`, `CLAUDE.md`, rule directory를 읽는다.
3. helper로 연결 후보와 근거를 확인한다.

```bash
python3 <knowns-root>/scripts/inspect_context.py \
  --project <project-root> \
  --json
```

4. project 규칙 또는 machine-local registry가 canonical Git remote로 명시 연결한 namespace만 후보로 인정한다.
5. v2 위키는 owning `.system/knowledge-contract.json`의 schema/template/validator와 registry의 `canonical_write_target`을 사용한다. 읽기 범위나 `my-wiki` 연결을 쓰기 대상으로 해석하지 않는다.
6. 후보가 없으면 `no-explicit-wiki-link`로 종료한다. 여러 후보면 별도 질문하지 말고 추천 대상과 대안을 단일 묶음에 포함한다.

세부 탐색은 [`references/rule-discovery.md`](references/rule-discovery.md)를 따른다.

### 2. wiki 규칙과 기존 지식 읽기 — read-only

추천 wiki를 helper에 넘긴다.

```bash
python3 <knowns-root>/scripts/inspect_context.py \
  --project <project-root> \
  --wiki <wiki-path> \
  --json
```

다음 자료와 그 자료가 명시적으로 참조한 규칙을 읽는다.

- `AGENTS.md`, `CLAUDE.md`
- `.claude/rules/**`, `.agents/rules/**`, `.codex/rules/**`
- `README*`, `SCHEMA*`, `GOVERNANCE*`, `CONTRIBUTING*`
- ingest, compile, maintenance, runbook, source-authority, contradiction, index 규칙
- 지정 lint/check/compile/deploy script

index와 이번 주제의 기존 note만 읽고 wiki 전체를 재귀 탐색하지 않는다.

### 3. 후보와 추천 plan 만들기

다음을 근거와 함께 분류한다.

| 구분 | 내용 |
|---|---|
| 사실·결정 | diff와 사용자 승인으로 검증된 상태 |
| 의미·목표 | 작업물이 필요한 이유와 도달할 상태 |
| 기여·성공 | 사용자·업무·시스템 가치와 성공 기준 |
| 판단 근거 | 선택 이유 |
| 검증 | test/build/E2E/운영 증거 |
| 이탈·미결 | deviation, blocker, provisional 항목 |
| 연결 | supports, implements, supersedes, depends-on, contradicts, extends |
| 제외 | secret, PII, code dump, transient, duplicate, unverified |

기존 정본에 병합 가능한지 먼저 보고, 새 주제일 때만 새 note를 추천한다.

- 같은 주장·적용 범위는 기존 주제에 병합하고 출처와 stable ID를 보존한다. 같은 내용이면 no-op이다.
- 대체 관계는 실제 날짜·버전·확정 근거로 판정한다. 다른 고객·환경·기간의 지식은 적용 범위를 구분하고, 어느 쪽이 맞는지 불명확하면 contested로 제안한다. 문체나 모델 confidence로 승자를 정하지 않는다.
- 검토 기한이 지났거나 양식만 바꾼 문서를 새로 검증했다고 표시하지 않는다. 인접한 관련 문서까지만 대조하며 raw나 위키 전체를 청소하지 않는다.
- 위 판정과 정확한 diff를 아래 단일 묶음에 포함한다. 적용 전에 문서의 base version을 다시 대조하고, 달라졌으면 새 근거로 재검토한다. 별도 curator skill이나 추가 승인 단계를 만들지 않는다.

[`assets/candidate-review.template.md`](assets/candidate-review.template.md)를 사용해 다음을 한 화면에 제시한다.

- 추천 wiki와 연결 근거
- 넣을 것, 제외할 것, 기존 연결과 status
- 의미, 목표, 기여, 성공 상태의 AI 추천 문장
- 생성·갱신할 정확한 파일과 link/index/log 변화
- compile/lint/check/deploy 명령
- wiki Git root, 파일 목록, commit message, branch, remote, credential-redacted URL, 새 branch와 base SHA
- 저장하지 않을 내용과 이유

### 4. 단일 묶음 선택 — 한 번만 STOP

아래 한 질문만 하고 기다린다.

> 위 추천안과 표시한 wiki write·검증·commit·push·배포 계획을 어떻게 처리할까요? `추천대로`, `수정: <모든 수정사항>`, `wiki 스킵` 중 하나로 답해주세요.

- `추천대로`, `추천순`, `추천안으로`, 동등한 표현은 모두 추천안 전체 승인으로 처리한다.
- `수정:` 답변에서 지정하지 않은 값은 추천안을 유지한다. 여러 후속 질문으로 쪼개지 않는다.
- `wiki 스킵`, `스킵`, `안 함`이면 즉시 종료하고 다시 묻지 않는다.
- 질문한 turn에서는 write를 계속하지 않는다.

### 5. ingest

스킵이 아닌 답을 받으면 추가 질문 없이 [`references/ingest-modes.md`](references/ingest-modes.md)에서 대상 mode를 선택해 실행한다.

- raw/source가 필요한 wiki는 선택된 source snapshot을 새 파일로 추가한 뒤 수정·이동·삭제하지 않는다.
- 기존 정본을 먼저 갱신하고 새 주제일 때만 새 note를 만든다.
- 출처, Git SHA, 날짜, status, sensitivity, review metadata는 wiki schema를 따른다. v2는 위키가 소유한 공통 양식·검증기로 자동 ingest와 동일하게 처리하고, security_domain과 customer_scope를 보존한다.
- `my-wiki`는 명시 읽기 연결이 있어도 knowns의 생성·수정 대상이 아니다. 연결된 정본 쓰기 디렉터리 밖으로 확대하지 않는다.
- 충돌은 조용히 덮지 않고 contested/contradiction 절차를 따른다.
- index·log·manifest·HANDOFF가 계약에 포함되면 같은 pass에서 갱신한다.
- 승인된 단일 묶음 범위 밖 변경이 필요하면 write를 멈추고 `blocked`로 보고한다.

### 6. 검증 → commit → push → deploy

1. wiki가 지정한 compile/lint/check를 실행한다.
2. note가 index에서 도달 가능하고 source reference와 link가 유효한지 확인한다.
3. 단일 묶음 plan과 실제 diff가 일치하는지 확인한다.
4. local Git wiki이면 project와 wiki의 Git common directory가 다른지 확인한다.
5. 승인 파일을 `--path`로 열거해 preflight를 실행한다.

```bash
python3 <knowns-root>/scripts/publish_git.py \
  --repo <wiki-git-root> \
  --project-repo <project-git-root> \
  --path <approved-file> \
  --message "<recommended-or-user-edited-message>" \
  --remote <remote> \
  --remote-url "<credential-redacted-url>" \
  --branch <branch> \
  --dry-run
```

6. 성공하면 같은 명령에 `--preflight-token <token>`을 넣어 non-force commit·push한다. 추천 plan에 새 branch와 정확한 base SHA가 있으면 `--allow-new-branch --new-branch-base <sha>`를 함께 사용한다.
7. push 뒤 wiki 규칙의 deploy command 또는 자동 배포 상태를 확인하고 배포 결과를 검증한다. deploy가 없는 wiki는 `not-applicable`로 기록한다.
8. preflight 이후 변경, remote race, push/deploy 실패가 생기면 force 복구하지 말고 `blocked`로 보고한다.

추가 commit·push·deploy 확인은 묻지 않는다.

### 7. 완료 보고

```text
KNOWNS: ingested | no-op | skipped | blocked
WIKI: <resolved path or none>
MEANING: <selected meaning>
FILES: <created/updated>
LINKS: <added/changed>
EVIDENCE: <validation and production deployment evidence>
GIT: <commit sha and remote branch | not-applicable | blocked reason>
DEPLOY: <verified target/status | not-applicable | blocked reason>
EXCLUDED: <not stored>
NEXT: <remaining recovery only>
```

## 검증 게이트

- [ ] 운영배포 성공 증거가 있다.
- [ ] explicit wiki connection과 governing rules를 확인했다.
- [ ] 단일 묶음에 후보·추천·exact write/publish/deploy plan을 모두 표시했다.
- [ ] 사용자 답이 `추천대로`, 일괄 수정, 스킵 중 하나다.
- [ ] 스킵이면 어떤 write도 하지 않고 종료했다.
- [ ] 비밀·개인정보·코드 원문·unrelated change를 제외했다.
- [ ] project와 wiki repo를 분리하고 승인된 wiki 파일만 반영했다.
- [ ] 검증 뒤 preflight와 동일한 상태에서 non-force commit·push했다.
- [ ] wiki 배포 결과를 확인했거나 `not-applicable` 근거를 남겼다.

## 장애 처리

- 연결 wiki 없음: `no-explicit-wiki-link`로 종료한다.
- 운영배포 증거 없음: 묻지 않고 `not-after-production`으로 종료한다.
- dirty/staged 충돌, remote race, 권한·검증·배포 실패: 자동 우회하지 말고 `blocked`로 보고한다.
- 승인 범위 밖 변경 필요: 추가 write를 멈추고 현재 상태와 필요한 복구만 보고한다.
