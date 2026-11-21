# 2026-11-21 Flowpass 입력 규칙: 쓰기 호출 전 규칙 전달 hook

## 목표 / 확정 사항
- Flowpass MCP로 내용을 입력할 때마다 정해진 작성 규칙을 에이전트가 반드시 읽게 한다.
- 규칙 본문은 md 파일 하나로 두고, 읽기를 모델의 기억이 아니라 hook이 강제한다.
- Claude와 Codex에 같은 정의로 설치한다.

## Gate evidence
- 사용자 요청(2026-11-21): "플로우패스 MCP 스킬로 뭔가 내용입력할때마다 글로벌룰로 아래 내용 md로 해서 무조건 읽게 하네스 및 룰 세팅 해줘" + 규칙 본문. 이어서 "ㄱㄱ".
- 설치·검증 보고 뒤 사용자 답(2026-11-21): "ㅇㅇ 맥북까지 싹 해놔" — commit·push와 두 번째 Mac 반영.
- 확인 질문: 없음. 규칙 본문·대상(Flowpass 입력)·방식(md + 하네스)이 요청에 있다.
- 승인된 범위: 규칙 md, hook, hook 등록, 전역 규칙 한 줄, 테스트, 문서, bootstrap 설치, commit·push, 두 번째 Mac의 pull·bootstrap·Codex 신뢰 등록.
- 미승인 가정: 없음.

## Issue tracking
- 대표: 생략. 열린 이슈가 없고 한 세션에서 끝나는 설정 추가다.

## 계획
1. `global/flowpass-input-rules.md`에 규칙 본문을 둔다.
2. `hooks/flowpass-input-rules.mjs`가 Flowpass MCP 쓰기 호출을 요청마다 한 번 거부하고 규칙을 거부 사유로 전달한다.
3. `global/governance-hooks.json`에 등록하고 `manifest.json`으로 규칙 파일을 hook 옆에 연결한다.
4. `node --test`, `public_audit.py`, `validate_skills.py`, bootstrap dry-run으로 검증하고 설치한다.
5. 설치된 세션에서 실제 Flowpass 쓰기 호출이 막히는지 확인한다.

## 판단 근거
- `additionalContext` 대신 거부(deny)를 택했다. PreToolUse의 `additionalContext`는 도구 결과 옆에 붙어 첫 호출의 내용이 이미 저장된 뒤에 보인다. 거부는 서버에 닿기 전에 규칙을 보여 준다.
- 전달 단위는 사용자 요청 하나다(Claude `prompt_id`, Codex `turn_id`). 호출마다 거부하면 통과 조건이 없어 입력이 불가능하다.
- 조회 도구 목록만 예외로 두고 나머지는 입력으로 본다. 플러그인이 쓰기 도구를 추가해도 빠지지 않는다. 조회 도구가 추가되면 한 번 재시도하는 비용만 든다.
- 같은 메시지에서 함께 나온 쓰기 호출은 규칙을 보기 전에 작성됐으므로, 전달 직후 4초 안에 도착한 호출도 거부한다.
- subagent는 context가 따로라서 `agent_id`별로 전달한다.
- 규칙 파일을 읽지 못하거나 상태를 저장하지 못하면 막지 않고 사용자에게 경고만 띄운다. 상태를 못 쓰는데 거부하면 Flowpass 입력이 영구히 막힌다.
- 규칙 파일은 `~/.claude/hooks/`에 symlink로 둔다. 정본을 고치면 bootstrap 없이 바로 반영된다.
- 작업 위치는 primary checkout의 main이다. 개인 동기화 저장소이고 bootstrap 링크가 이 checkout을 가리킨다.

### 기각안
- `~/.claude/rules/`에 두어 항상 로드: 모든 세션의 응답 규칙이 되어 "Flowpass 입력할 때"라는 범위를 벗어난다.
- UserPromptSubmit에서 "flowpass" 키워드로 주입: 키워드 없이 시작되는 입력을 놓친다.
- Skill 도구 호출에 주입: Codex에는 Skill 도구가 없고, skill 없이 MCP를 직접 부르는 경로를 놓친다.

## ⚠️ DEVIATION
- 없음

## 변경
- `global/flowpass-input-rules.md`: 규칙 본문(사용자 제공 원문, 절 제목만 붙임).
- `hooks/flowpass-input-rules.mjs`: Flowpass MCP 입력 호출을 요청마다 한 번 거부하고 규칙 전문을 거부 사유로 전달.
- `global/governance-hooks.json`: `PreToolUse` matcher `^mcp__.*flowpass.*` 등록.
- `manifest.json`: 규칙 파일을 `~/.claude/hooks/flowpass-input-rules.md`로 연결.
- `global/CLAUDE.md`: 규칙 파일을 가리키는 한 줄(hook이 닿지 않는 경로는 직접 읽기).
- `tests/hook-flowpass-input-rules.test.mjs`, `docs/hook-behavior.md`, README hook 표·구조도·이력 링크, HANDOFF.

## 검증
- `node --test tests/*.test.mjs`: 91 pass(신규 9).
- `python3 -m unittest discover -s tests -p 'test_*.py'`: 96 OK. `validate_skills.py` 26 skills 통과. `bash -n` 통과. JSON 유효.
- `python3 scripts/public_audit.py --history`: 실패 2건. 로컬 denylist가 기존 agent-bot 참고 문서의 tree와 history 한 commit에 걸린다. 이번 변경 파일은 걸리지 않았고, HANDOFF에 이미 기록된 문제다. CI의 같은 단계는 2026-11-03 실행부터 이 건으로 실패하고 있다.
- bootstrap: 빈 홈 dry-run 통과. 실제 설정 사본에 적용해 비교하니 hook 등록 1건만 추가되고 다른 hook과 설정은 그대로였다. 실제 설치 뒤 `--status` 정상 82개.
- Claude 실측(설치한 세션): `flowpass_check` 첫 호출이 보류되며 규칙 전문이 돌아왔다. `flowpass_guide` 조회는 보류 없이 실행됐다. 10초 뒤 `flowpass_check` 재호출은 실행됐다.
- Codex 실측: `codex_hook_trust.py --apply`로 새 hook 1건을 신뢰 등록했다(`review_required` 1 → 0). 임시 로컬 MCP 서버의 `mcp__flowpass_hookcheck__flowpass_write`가 1차 보류, 2차 실행됐고 서버에 닿은 호출은 1건이다. 실제 Flowpass 도구 `mcp__flowpass__flowpass_check`(인자 없는 요건 조회)도 1차 보류, 2차 실행됐다.
- 설치 전 `bootstrap --status`는 Claude·Codex hook manifest 2건이 갱신 필요였고 Codex 관리 hook 5건이 `modified` 상태였다. 설치와 신뢰 등록 뒤 둘 다 0건이다.

## 다음에 참고
- Codex는 MCP 도구를 code-mode의 `tools.<name>()`으로 호출한다. `codex exec`로 검증할 때 "도구를 호출하라"고만 하면 모델이 도구가 없다고 답한다. `ALL_TOOLS`에서 이름을 찾게 하고 호출 형태를 지정한다.
- `codex exec`는 stdin을 `< /dev/null`로 닫고 실행한다. 열어 둔 첫 실행은 4분 안에 끝나지 않았다(원인은 stdin 대기로 추정, 미확인).
- 규칙 본문을 고칠 때는 `global/flowpass-input-rules.md`만 수정한다. symlink라 다음 호출부터 반영된다.
- 조회 도구가 플러그인에 추가되면 `LOOKUP_TOOLS`에 넣는다. 넣지 않아도 한 번 재시도될 뿐 막히지는 않는다.
