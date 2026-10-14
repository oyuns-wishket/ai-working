# Paseo 제목 fallback을 CLI 이름 변경으로 (2026-10-14)

## 목표 / 확정 사항
- 사용자 보고: 고객 ERP 프로젝트의 Paseo 워크스페이스 제목이 계속 영어로 생긴다.
- 2026-10-13 작업([Paseo 자동 제목 한국어화](2026-10-13-paseo-korean-title-style.md))의 후속 결함 수정이다.

## Gate evidence
- 사용자 요청·답변: 위 보고. 원인 조사와 수정을 요청한 것으로 본다.
- 확인 질문: 없음. 기존 hook의 결함 수정이고 되돌리기 쉽다.
- 승인된 범위: ai-working의 `hooks/paseo-title.mjs`, 테스트, 문서. 개인 동기화 저장소라 main 직접 반영이 허용된다.
- 미승인 가정: 고객 repo의 제목 지시문 PR merge(그 프로젝트의 통합 절차 소관), 기존 영어 제목 일괄 변경, Paseo daemon 설정 변경.

## Issue tracking
- 대표: 생략 — 개인 SSOT 저장소의 hook 결함, 열린 관련 이슈 없음(`gh issue list --search paseo` 0건).
- 완료 시점: main 반영 + bootstrap 후 실제 Paseo 세션에서 이름 변경 확인.

## 원인 (실측)
1. 해당 고객 repo의 `paseo.json`에 제목 지시문이 없다. 지시문을 넣은 PR(2026-10-13 생성)이 통합 브랜치에
   merge되지 않아 main checkout 디스크 파일에 반영되지 않았다. 그래서 Paseo가 기본 영어 지시문으로 제목을 만든다.
2. 대신 들어가야 할 hook fallback이 동작하지 않았다.
   - Claude 세션: 그 repo의 오늘 세션 5개 모두 `[Paseo 제목]` 알림을 받았지만 `rename_workspace` 호출은 0건이다.
     daemon 설정이 `daemon.mcp.injectIntoAgents: false`라 Paseo MCP가 agent에 주입되지 않는다. 알림의
     "Paseo MCP가 없으면 건너뛴다"에 따라 매번 조용히 건너뛰었다. 어제의 "rename_workspace 성공" 검증이 어떤
     경로였는지는 Claude 세션 기록에서 확인되지 않는다(`mcp__paseo` 호출 기록 0건).
   - Codex 세션: 알림은 들어갔지만(메인 스레드 1건) 호출 0건. 같은 이유로 MCP가 없다.
3. 실행 중인 daemon은 Homebrew CLI `@getpaseo/cli` 0.10.3(앱 번들 0.11.2와 다름)이다. 0.10.3도
   `paseo.json`의 `metadataGeneration.title.instructions`를 읽는 것을 소스로 확인했다.

## 계획
- 알림이 Paseo MCP 대신 `paseo workspace rename <workspaceId> "<제목>"` CLI를 쓰게 한다. hook이 이미
  workspaceId를 알고 있으므로 명령을 완성해서 준다. `paseo`가 PATH에 없으면 알림을 내지 않는다.
- 테스트: 알림에 workspaceId가 담긴 CLI 명령이 들어가는지, CLI가 없을 때 침묵하는지.
- 검증: `node --test`, 실제 Paseo에서 새 워크스페이스 → 알림 → CLI 이름 변경 확인.

## 판단 근거
- CLI 실측: 이 세션에서 `paseo workspace rename wks_… "Paseo 한글 제목"`이 성공했다(Claude, 샌드박스 없음).
- 덮어쓰기 경합: daemon의 `applyGeneratedWorkspaceTitle`은 현재 제목이 비었거나 첫 프롬프트 placeholder와
  같을 때만 생성 제목으로 바꾼다. agent가 먼저 이름을 바꾸면 늦게 도착한 영어 제목이 덮어쓰지 않는다.
- 기각: `daemon.mcp.injectIntoAgents: true`로 전환 — 모든 agent에 Paseo MCP 전체 도구(agent 생성·삭제 등)가
  붙어 권한 표면이 커지고 장비별 daemon 설정이라 SSOT로 관리되지 않는다.
- 기각: hook이 직접 이름을 짓기 — 첫 요청이 SessionStart 시점에 없고 모델 호출 비용·지연이 생긴다.
- 기각: hook이 `paseo.json`을 써 넣기 — 시작 hook은 작업 트리를 건드리지 않는다는 기존 원칙.

## 변경
- `hooks/paseo-title.mjs`: 알림이 workspaceId를 채운 `paseo workspace rename` 명령을 준다. sandbox에서 daemon에
  연결하지 못하면 권한 상승으로 재시도하라고 적었다. `paseo`가 PATH에 없거나 workspaceId가 단순 식별자가
  아니면 알림을 내지 않는다(명령 문자열에 그대로 들어가기 때문).
- `tests/hook-paseo-title.test.mjs`: fixture에 가짜 `paseo` 실행 파일을 두고, 명령 형식·CLI 부재·비정상 id 사례를 추가.
- `docs/hook-behavior.md`: CLI 사용 이유, sandbox 재시도, 생성 제목이 늦게 와도 덮어쓰지 않는 근거.

## 검증
- `node --test tests/*.test.mjs` 53건, `python3 -m unittest` 90건, `validate_skills.py`(24 skills),
  `public_audit.py --history` 모두 통과.
- 실제 Paseo E2E(수정 hook을 설치본에 임시로 덮어쓴 뒤 원복):
  - Claude(haiku, 기본 권한 모드): 새 워크스페이스에서 agent가 알림대로
    `paseo workspace rename <id> "현금영수증 취소"`를 실행 → 제목이 바뀌고 5초 뒤에도 유지.
  - Codex(auto-review, workspace-write sandbox): 1차 실행은 daemon 연결 실패 → agent가 권한 상승을 요청 →
    허용 후 제목이 "로그인 실패 조사"로 바뀜.
  - 두 경우 모두 Paseo 생성 제목(영어)이 나중에 덮어쓰지 않았다.
  - 테스트 agent·워크스페이스는 삭제·보관했다.
- 사전 확인: `codex sandbox`(workspace-write)에서 `paseo workspace ls`가 `DAEMON_NOT_RUNNING`으로 실패하는 것을
  재현해 알림 문구에 재시도 지시를 넣었다.

## ⚠️ DEVIATION
- ⚠️ 계획에 없던 "sandbox 실패 시 권한 상승 재시도" 문구 추가 → 대응: Codex 기본 모드에서 CLI가 daemon에 접속하지
  못하는 것을 실측해 반영. 권한 상승은 사용자 승인을 거치는 기존 경로라 승인 경계는 그대로다 → 리뷰: 자체 확인.
- ⚠️ 권한 확인을 요구하는 모드(Claude 기본·auto, Codex auto-review)에서는 제목 변경마다 승인 요청이 한 번 뜬다.
  allowlist 추가는 권한 표면 확대라 이번 범위에서 하지 않았다 → 리뷰: 사용자 결정 필요(완료 보고에 포함).

## 남은 일
- 고객 repo의 제목 지시문 PR이 merge되면 그 repo는 Paseo가 처음부터 한국어 제목을 만든다(hook은 그때 침묵).
- 이미 영어로 생긴 기존 워크스페이스 제목은 바꾸지 않았다.

## 다음에 참고
- Paseo MCP 도구는 daemon `mcp.injectIntoAgents`가 켜져 있을 때만 agent에 보인다. MCP를 전제로 한
  지시는 이 설정을 먼저 확인한다.
- "있으면 하고 없으면 건너뛴다"형 지시는 실패가 조용하다. 검증은 실제 사용 환경의 도구 목록으로 한다.
