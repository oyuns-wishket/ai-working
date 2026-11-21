# 2026-11-21 Flowpass 입력 규칙: 쓰기 호출 전 규칙 전달 hook

## 목표 / 확정 사항
- Flowpass MCP로 내용을 입력할 때마다 정해진 작성 규칙을 에이전트가 반드시 읽게 한다.
- 규칙 본문은 md 파일 하나로 두고, 읽기를 모델의 기억이 아니라 hook이 강제한다.
- Claude와 Codex에 같은 정의로 설치한다.
- Flowpass는 첫 번째 Mac에서만 쓴다. 두 번째 Mac에는 Flowpass를 연결하지 않는다(2026-11-21 사용자 결정).

## Gate evidence
- 사용자 요청(2026-11-21): "플로우패스 MCP 스킬로 뭔가 내용입력할때마다 글로벌룰로 아래 내용 md로 해서 무조건 읽게 하네스 및 룰 세팅 해줘" + 규칙 본문. 이어서 "ㄱㄱ".
- 설치·검증 보고 뒤 사용자 답(2026-11-21): "ㅇㅇ 맥북까지 싹 해놔" — commit·push와 두 번째 Mac 반영.
- 두 번째 Mac 상태 보고 뒤 사용자 답(2026-11-21): "근데 어차피 맥북에서 쓸일 없어 여기만 잘 세팅해놓자 ssot 에도 반영해줘" — Flowpass 사용 장비를 첫 번째 Mac으로 한정하고 기록에 반영.
- 확인 질문: 없음. 규칙 본문·대상(Flowpass 입력)·방식(md + 하네스)이 요청에 있다.
- 승인된 범위: 규칙 md, hook, hook 등록, 전역 규칙 한 줄, 테스트, 문서, bootstrap 설치, commit·push, 두 번째 Mac의 pull·bootstrap. 두 번째 Mac의 Flowpass 연결과 Codex 신뢰 등록은 위 결정으로 범위에서 빠졌다.
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
- 같은 메시지에서 함께 나온 쓰기 호출은 규칙을 보기 전에 작성됐으므로, 전달 직후 1.5초 안에 도착한 호출도 거부한다. 실측에서 동시 호출은 0.1초 간격으로, 재시도는 보류 2.1초·2.5초 뒤에 도착했다. 처음 정한 4초는 모든 재시도를 한 번 더 막았다.
- subagent는 context가 따로라서 `agent_id`별로 전달한다.
- 규칙 파일을 읽지 못하거나 상태를 저장하지 못하면 막지 않고 사용자에게 경고만 띄운다. 상태를 못 쓰는데 거부하면 Flowpass 입력이 영구히 막힌다.
- 규칙 파일은 `~/.claude/hooks/`에 symlink로 둔다. 정본을 고치면 bootstrap 없이 바로 반영된다.
- 작업 위치는 primary checkout의 main이다. 개인 동기화 저장소이고 bootstrap 링크가 이 checkout을 가리킨다.

### 기각안
- `~/.claude/rules/`에 두어 항상 로드: 모든 세션의 응답 규칙이 되어 "Flowpass 입력할 때"라는 범위를 벗어난다.
- UserPromptSubmit에서 "flowpass" 키워드로 주입: 키워드 없이 시작되는 입력을 놓친다.
- Skill 도구 호출에 주입: Codex에는 Skill 도구가 없고, skill 없이 MCP를 직접 부르는 경로를 놓친다.

## ⚠️ DEVIATION
- ⚠️ 두 번째 Mac의 Codex 신뢰 등록을 적용하지 않았다 → 대응: 그 장비의 Codex에는 ai-working hook의 신뢰 기록이 없어, `codex_hook_trust.py --apply`가 새 hook 1건이 아니라 가드 11건을 한꺼번에 처음 켠다. 승인받은 범위(새 hook 반영)보다 큰 변경이라 상태만 기록했다 → 리뷰: 사용자 결정(2026-11-21). 그 장비에서는 Flowpass를 쓰지 않으므로 적용하지 않는다.

## 변경
- `global/flowpass-input-rules.md`: 규칙 본문(사용자 제공 원문, 절 제목만 붙임).
- `hooks/flowpass-input-rules.mjs`: Flowpass MCP 입력 호출을 요청마다 한 번 거부하고 규칙 전문을 거부 사유로 전달.
- `global/governance-hooks.json`: `PreToolUse` matcher `^mcp__.*flowpass.*` 등록.
- `manifest.json`: 규칙 파일을 `~/.claude/hooks/flowpass-input-rules.md`로 연결.
- `global/CLAUDE.md`: 규칙 파일을 가리키는 한 줄(hook이 닿지 않는 경로는 직접 읽기).
- `tests/hook-flowpass-input-rules.test.mjs`, `docs/hook-behavior.md`, README hook 표·구조도·이력 링크, HANDOFF.

## 검증
- `node --test tests/*.test.mjs`: 91 pass(신규 9). 재시도 창을 줄인 뒤에도 91 pass다.
- `python3 -m unittest discover -s tests -p 'test_*.py'`: 96 OK. `validate_skills.py` 26 skills 통과. `bash -n` 통과. JSON 유효.
- `python3 scripts/public_audit.py --history`: 실패 2건. 로컬 denylist가 기존 agent-bot 참고 문서의 tree와 history 한 commit에 걸린다. 이번 변경 파일은 걸리지 않았고, HANDOFF에 이미 기록된 문제다. CI의 같은 단계는 2026-11-03 실행부터 이 건으로 실패하고 있다.
- bootstrap: 빈 홈 dry-run 통과. 실제 설정 사본에 적용해 비교하니 hook 등록 1건만 추가되고 다른 hook과 설정은 그대로였다. 실제 설치 뒤 `--status` 정상 82개.
- Claude 실측(설치한 세션): `flowpass_check` 첫 호출이 보류되며 규칙 전문이 돌아왔다. `flowpass_guide` 조회는 보류 없이 실행됐다. 10초 뒤 `flowpass_check` 재호출은 실행됐다.
- Codex 실측: `codex_hook_trust.py --apply`로 새 hook 1건을 신뢰 등록했다(`review_required` 1 → 0). 임시 로컬 MCP 서버의 `mcp__flowpass_hookcheck__flowpass_write`가 1차 보류, 2차 실행됐고 서버에 닿은 호출은 1건이다. 실제 Flowpass 도구 `mcp__flowpass__flowpass_check`(인자 없는 요건 조회)도 1차 보류, 2차 실행됐다.
- 새 Claude Code 세션 실측(재시도 창 4초): 첫 호출 보류, 2.1초 뒤 재시도도 보류, 4.1초 뒤 세 번째 호출이 실행됐다. 창을 1.5초로 줄여 재설치한 뒤에는 동시 호출 2건이 보류되고 첫 재시도가 실행됐다. Codex도 재설치 뒤 기다리지 않고 재시도한 실제 Flowpass 호출이 1차 보류, 2차 실행이었다.
- 설치 전 `bootstrap --status`는 Claude·Codex hook manifest 2건이 갱신 필요였고 Codex 관리 hook 5건이 `modified` 상태였다. 설치와 신뢰 등록 뒤 둘 다 0건이다.

## 공개와 장비별 상태
- push: 이번 변경만 골라 올렸다. 같은 checkout에 있던 다른 세션의 미커밋 작업은 그대로 두었다.
- CI `public-safety`: 이번 작업의 commit마다 감사 단계에서 실패했다. 지목된 파일은 위 검증 항목의 기존 문서 한 건이고, 그 단계에서 멈춰 뒤의 테스트 단계는 실행되지 않았다.
- 첫 번째 Mac(Flowpass 사용 장비): bootstrap `--status` 정상 82개, Codex 관리 hook 11건 모두 `trusted`. Claude Code와 Codex 모두 실제 Flowpass 도구 호출로 보류와 재시도 통과를 확인했다.
- 두 번째 Mac(Flowpass 미사용):
  - 저장소를 fast-forward하고 bootstrap을 적용했다. hook은 설치됐지만 Flowpass MCP 서버가 없어 발화하지 않는다. 설치본에 넣은 모의 호출은 보류, 조회 통과, 재시도 통과였다.
  - Codex가 관리 hook 11건을 한 번도 신뢰한 적이 없다. 11건의 현재 hash는 첫 번째 Mac과 같고 그 장비의 신뢰 hash 14건 어디에도 없다. 그 장비에서 Codex를 쓰려면 먼저 `codex_hook_trust.py --apply`를 실행한다.
  - 자원 가드 테스트 파일이 쉬었다가 처음 돌릴 때 3번 실패했고 바로 이어 돌린 2번은 통과했다. dev server 작업 폴더가 `unknown`으로 나온다. hook과 테스트는 이번 작업에서 바뀌지 않았다. `lsof` 조회의 300ms 제한을 첫 실행이 넘긴다고 추정한다.
  - 덮개를 닫은 배터리 상태에서는 절전과 깨어남을 반복해 원격 접속이 자주 끊긴다.

## 다음에 참고
- bootstrap과 작업 앱은 각자 자기 hook을 이벤트의 끝에 다시 붙인다. 작업 앱이 hook을 다시 등록하면 순서가 바뀌어 Codex의 위치 기반 신뢰 키가 밀리고, 밀린 hook은 Codex에서 실행되지 않는다. 첫 번째 Mac의 bootstrap 백업 5개 중 4개가 이 상태였고, 이번 설치 전에도 관리 hook 5건이 `modified`였다. `bootstrap --status`가 hook manifest 갱신 필요를 알리면 `./bootstrap.sh`를 실행한다. 순서가 돌아오며 기존 신뢰가 복구된다(이번 설치에서 5건이 그렇게 복구됐다). Claude Code에는 신뢰 단계가 없어 영향이 없다.
- 다른 장비 작업은 스크립트를 올려 분리 실행하고 로그의 종료 표식을 기다린다. 연결이 끊겨도 원격 실행이 끝까지 간다.
- Codex hook hash는 정의가 같으면 장비와 CLI 버전(0.154, 0.160)이 달라도 같다. 다른 장비의 신뢰 여부는 hash로 대조한다.
- Codex는 MCP 도구를 code-mode의 `tools.<name>()`으로 호출한다. `codex exec`로 검증할 때 "도구를 호출하라"고만 하면 모델이 도구가 없다고 답한다. `ALL_TOOLS`에서 이름을 찾게 하고 호출 형태를 지정한다.
- `codex exec`는 stdin을 `< /dev/null`로 닫고 실행한다. 열어 둔 첫 실행은 4분 안에 끝나지 않았다(원인은 stdin 대기로 추정, 미확인).
- 규칙 본문을 고칠 때는 `global/flowpass-input-rules.md`만 수정한다. symlink라 다음 호출부터 반영된다.
- 조회 도구가 플러그인에 추가되면 `LOOKUP_TOOLS`에 넣는다. 넣지 않아도 한 번 재시도될 뿐 막히지는 않는다.
