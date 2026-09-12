---
name: agent-bot-setup
description: Build, connect, or upgrade a project or organization chat bot that works like a persistent terminal coding agent with direct investigation and OS-enforced code-edit and deployment blocking. Use for "프로젝트 봇 세팅", "조직 봇 연결", "에이전트 봇", or "봇을 터미널 에이전트처럼".
---

# Agent Bot Setup

사용자가 채팅에서 **에이전트와 직접 대화하는 방식으로 조사**할 수 있는 봇을 구현한다. 대상 조직의 데이터·인증·인프라를 연결하며 새 설치와 기존 봇의 품질 개선에 모두 사용한다. Claude Code와 Codex가 같은 절차를 수행한다.

## 반드시 유지할 동작

- 채팅은 입출력 창구, **native Codex app-server가 실제 agent loop**다. 모델 응답만 relay하거나 매 메시지마다 세션을 버리는 고정 4회 JSON 조사 루프로 대신하지 않는다.
- 조직·프로젝트·채널·스레드별 대화와 도구 결과를 유지한다. “그럼 그건 왜?”에도 앞선 근거를 이어 사용한다. 이미지 내용은 실제 이미지 입력으로 전달한다.
- 허용 채널의 시스템 이상 제보는 멘션·물음표·“수정해줘” 없이도 조사하고 답한다. 공용 채널 일상 대화는 조용히 처리할 수 있고, DM의 직접 질문에는 답한다.
- **코드 수정·배포는 실행 권한으로 차단**한다. 프롬프트만으로 금지하지 않는다. 읽기 전용 shell과 host의 허용 데이터/로그 도구는 제공한다.
- 실제 읽기 진행을 알리고 답변 의무를 저장한다. 조사 시작 후 최종 `ignore`, 재시작, timeout 때문에 조용히 사라지지 않는다. 결과가 불확실하면 확인 범위와 부족한 근거를 답한다.
- 채팅 답변과 선택적 업무 접수는 host가 검증해 수행한다. 모델에게 raw Slack/GitHub/SSH/배포 명령권이나 자격증명을 주지 않는다. 이슈 접수는 대상 조직이 요청한 경우에만 연결한다.

## 기본값과 조직별 값

검증된 기본값은 아래 한 표를 사용한다. 상한은 비용·호스트 용량에 맞춰 조정할 수 있지만 실행 구조와 권한 계약은 유지한다.

| 항목 | 기본 / 적용 규칙 |
|---|---|
| Runtime | 설치된 Codex app-server의 버전·schema·feature를 시작할 때 probe하고 그 결과를 기록 |
| Model / effort | 대상 조직 계정에서 지원되는 모델과 effort를 확인하고, 확인 없이 다른 값으로 바꾸지 않음 |
| Chat | Slack Socket Mode 우선; 사용자가 다른 채팅 플랫폼을 정했으면 adapter만 맞추고 나머지 계약 유지 |
| 범위 | tenant/project/workspace/channel/thread별 host 검증·별도 세션; 고객 간 자격증명·도구·메모리 격리 |
| Native 권한 | named `agent-readonly`; 승인 never, shell network off, 검증한 source projection과 최소 runtime 파일만 read |
| 조사 한도 | 기본900초, host read80회/turn,100turn/일/tenant; 모델 HTTP 호출 횟수와 혼동하지 않음 |
| 동시 실행 | 작은 host는1개부터 실측; lease heartbeat와 대기 큐 유지 |
| 답변 | 질문에 맞는 깊이, 기본 최대6000자, 채팅 플랫폼 block 한도에 맞춰 나누되 조건을 자르지 않음 |
| 가변 값 | 조직 소유 auth, 프로젝트·채널, source/문서, DB read role/views, 정제 로그, bot 이름, 운영 host, 접수 backend |

## 1. 대상 확인 [AI]

기존 repo 규칙·봇 경로·서비스 상태·허용 인프라를 확인한다. 이미 전달받은 값은 다시 묻지 않는다. 새 프로젝트에서는 접근 가능한 설정을 먼저 조사하고, 남은 핵심 값만 한 번에 확인한다.

- 어느 조직·프로젝트인가? 어떤 채팅과 허용 채널/사용자인가? 기존 봇 업그레이드인가?
- 어디서 실행하며 해당 조직이 소유한 인증은 어디에서 공급되는가?
- 무엇을 읽어야 원인을 확인할 수 있는가? 코드/문서/DB/실행 이력/로그의 실제 접근 여부는?
- 답변 외에 요청 접수가 필요한가? 기존 승인·배포 범위는 어디까지인가?

[`assets/bot-profile.example.json`](assets/bot-profile.example.json)을 대상 repo의 **비밀값 없는** 실행 프로필로 구체화한다. 예시 값은 실제 tenant 식별자로 교체하며 토큰·OAuth JSON·DB DSN을 넣지 않는다. 기존 고객 계정·개인 credential vault·다른 조직의 봇 state를 가져오지 않는다. 외부 인증 저장소는 대상 사용자가 소유하고 사용을 승인한 경우에만 adapter로 연결한다.

프로젝트 개발/배포 workflow가 있으면 따른다. 범위가 명확한 구현·읽기 검증은 진행하고, 이미 받은 운영 승인을 단계마다 반복해서 묻지 않는다. 이 스킬을 설치하라는 요청은 다른 조직에 앱을 설치하거나 메시지를 발송하라는 승인이 아니다.

## 2. 실행기 구현 [AI]

[`references/runtime-contract.md`](references/runtime-contract.md)를 읽고 아래 흐름을 연결한다. 이는 구현·검증 blueprint이며 특정 고객 저장소나 개인 비서 설치에 의존하지 않는다.

```text
Chat event → host의 인증·범위·queue → tenant/project/thread session
             → Codex native loop → 읽기 shell / host read tools
             → 근거 포함 답변 → 검증·중복 방지 outbox → 같은 대화
```

- 기존 봇이면 수신/접수/outbox 계약을 보존하고 실행 경로를 교체한다. 새 봇이면 tenant routing, durable queue/state, read adapters, publication을 구현한다.
- [`assets/agent-instructions.md`](assets/agent-instructions.md)를 조직의 용어와 접수 정책에 맞춘다. 실제 미연결 자료를 접근 가능하다고 쓰지 않는다.
- DB·로그는 이름이 있다는 것만으로 연결 완료가 아니다. 실제 권한·조회 성공·시각을 확인한다. 부족한 audit/log 경로는 구체적으로 기록하고 허용된 범위에서 연결한다. 한 조직의 제한된 dataset 구성을 범용 완성품으로 복제하지 않는다.
- native secret/state 경로와 읽기 workspace를 분리한다. 고객이 바뀌면 같은 CODEX_HOME/credential/budget/tool instance를 재사용하지 않는다.

## 3. 설치와 권한 검증 [AI / USER]

[AI] 대상 OS/CPU에 맞는 **전체** Codex package와 native executable을 설치하고 버전/공식 artifact checksum을 고정한다. bridge와 SDK의 요청 구조는 설치 버전의 schema로 확인한다. 외부 문서가 필요하면 OpenAI 공식 문서를 사용한다.

[USER] 조직 관리자 설치 승인, 브라우저 OAuth 동의, 제공할 수 없는 자격증명 발급만 수행한다. [AI]가 할 수 있는 CLI 작업을 사용자에게 넘기지 않는다.

[`scripts/runtime_guard.py`](scripts/runtime_guard.py)는 공통 named permission config와 **무인증·모델 호출0회** OS fixture probe를 제공한다.

```bash
python3 <skill-dir>/scripts/runtime_guard.py render --workspace <검증된-소스-사본> --binary <native-codex> --output <private-CODEX_HOME/config.toml>
python3 <skill-dir>/scripts/runtime_guard.py probe --binary <native-codex>
```

- Python3.9 이상에서 실행한다. 먼저 별도 private state 디렉터리를 mode0700으로 만든다. `render`는 실제 존재하는 경로와 manifest/hash를 검증하고 mode0600의 새 config만 생성한다. 기존 config를 덮지 않는다. 소스 사본 생성/검토는 host 구현의 책임이다.
- probe는 임시 fixture만 사용하고 자체 프로세스를 종료한다. 필요한 읽기 성공과 비허용 읽기/쓰기/network 실패를 **함께** 확인한다.
- 같은 binary·policy generator·service 계정·unit 강화 옵션으로 다시 probe한다. synthetic probe만 성공하고 실제 봇이 더 넓은 정책을 쓰면 통과가 아니다. 실제 thread/turn 설정과 도구 allowlist도 대조한다.
- Linux의 bundled bubblewrap, exact executable read, AF_NETLINK, 메모리 상한 함정은 runtime reference를 따른다. 원인을 해결하려고 full-access/승인 허용/secret 읽기로 바꾸지 않는다.

## 4. 실제 대화·격리·운영 검증 [AI]

[`references/acceptance.md`](references/acceptance.md)의 기능·권한·재시작·다른 tenant 사례를 수행한다. 운영 source/config와 합성 fixture 결과를 구분해서 기록한다.

먼저 읽기 전용 adapter와 별도 private state로 원문→후속 질문을 실행한다. 실제 발송 검증은 승인된 테스트 대상에서만 하며 “세팅” 요청을 모든 고객 채널에 시험 메시지를 보내라는 승인으로 해석하지 않는다.

프로젝트 build/lint/test와 실제 native 실행·권한·인증 검증 후 승인된 배포 범위까지 완료한다. 새 활성화가 필요하면 검증 결과와 정확한 전환/rollback을 먼저 준비한다. 배포 실패 보고 자체가 실패해도 복구가 실행되도록 만들고, 새 메시지가 쌓인 현재 DB를 과거 backup으로 덮지 않는다.

## 완료 보고

현재 live/미배포 상태, 실제 model/effort, 대화 지속·실제 이미지 검증, code/deploy 차단 증거, 연결한 자료와 미연결 자료, 설치 위치·rollback을 짧게 보고한다. 같은 실행 구조를 구현했다는 사실과 “터미널과 품질이 항상 동일하다”는 보장을 혼동하지 않는다. 설정 파일 생성이나 service active만으로 완성을 주장하지 않는다.
