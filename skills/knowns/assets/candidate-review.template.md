# knowns 단일 묶음 선택

## 대상

- Project: `<project-root>`
- Connected wiki: `<wiki-path>`
- Connection evidence: `<project rule:line>`
- Governing rules: `<files read>`
- Wiki Git root: `<separate git root or not-applicable>`
- Planned branch / remote: `<current-branch> / <remote-name> / <credential-redacted-url>`
- Deploy evidence: `<production URL/status/evidence>`
- Publish boundary: `단일 선택 후 표시한 wiki 파일만 검증→non-force commit/push→deploy`

## 넣을 후보

| 후보 | 제안 내용 | 근거 | 기존 연결 | 상태 |
|---|---|---|---|---|
| 사실 |  |  |  | verified/provisional |
| 결정 |  |  |  |  |
| 판단 근거 |  |  |  |  |
| 의미·목표 | `<AI 추천 문장>` | 현재 대화·검증 증거 |  | recommended |
| 기여·성공 상태 | `<AI 추천 문장>` | 현재 대화·검증 증거 |  | recommended |
| 검증 |  | command/output |  |  |
| 이탈·미결 |  | impl-note/HANDOFF |  |  |

## 제외 후보

| 내용 | 제외 이유 |
|---|---|
|  | secret/PII/code dump/transient/duplicate/unverified |

## exact write·publish·deploy plan

- Files: `<exact paths and changes>`
- Links/status/index/log: `<exact changes>`
- Validation: `<commands>`
- Commit: `<message>`
- Git: `<repo / branch / remote / redacted URL / new branch base>`
- Deploy: `<command or automatic pipeline and verification>`

## 한 번의 선택

위 추천안과 표시한 wiki write·검증·commit·push·배포 계획을 어떻게 처리할까요?

- `추천대로`: 모든 AI 추천을 적용하고 전체 pipeline 실행
- `수정: <모든 수정사항>`: 지정 항목만 바꾸고 나머지는 추천대로 실행
- `wiki 스킵`: write 없이 즉시 종료
