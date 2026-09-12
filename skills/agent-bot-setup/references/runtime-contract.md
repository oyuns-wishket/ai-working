# Native agent runtime contract

구현할 때 읽는다. 기본값은 SKILL.md의 표가 정본이다. 설치된 Codex binary의 schema와 실제 probe로 이 계약을 재검증한다. 고객 저장소나 특정 개인 OAuth 도구에 의존하지 않는다.

## 조직과 권한의 경계

Host가 검증한 `(tenant, project, chat_workspace, channel, thread)`로 session을 찾는다. 이벤트 서명/Socket Mode 설치 identity, 채널·사용자 허용 여부를 먼저 검증한다. 모델 인자나 메시지에 적힌 tenant ID로 credential/tool 범위를 바꾸지 않는다. 이벤트 중복 키도 tenant를 포함한다.

조직마다 credential, private state/CODEX_HOME, session registry, daily budget, 도구 인스턴스와 source projection을 분리한다. 서로 신뢰하지 않는 고객은 별도 service identity/실행 경계를 쓴다. DB key prefix만 다르게 하고 같은 privileged tool/credential을 공유하는 것으로 격리를 대신하지 않는다. Bot의 읽기 권한은 발신자의 접근 범위를 넘지 않아야 한다.

조직 소유의 지원되는 Codex 인증 경로를 확인한다. 기존 조직 계정의 native 인증 또는 host credential adapter를 사용할 수 있다. 외부 OAuth adapter라면 app-server `account/login/start` 계약을 설치 schema로 확인하고 토큰은 stdin으로만 보낸다. refresh 요청을 같은 계정으로 처리하고 account identity 변경 시 중단한다. 외부 credential 저장소는 대상 소유자가 명시한 범위에서만 사용한다. 토큰을 Git·프로필·argv·로그·model tool response에 넣지 않는다.

## 소스와 도구

Host가 승인한 코드·문서만 별도 source projection으로 복사한다. `.git`, `.env*`, credential, agent home, 실행 hook/plugin, 빌드 결과와 symlink/special file은 제외한다. 파일/확장자 allowlist, 개별/전체 용량 제한, secret 검토를 적용한다. 현재 코드와 문서가 개인정보를 포함할 수도 있으므로 확장자만으로 공개 가능하다고 간주하지 않는다.

Projection은 runtime 시작 전에 검증하고 실행 중에는 host 소유의 immutable release로 유지한다. writable live checkout을 그대로 mount하지 않는다. 업데이트는 새 projection으로 만들고 host가 검증 후 전환한다. Manifest는 내용의 동일성을 확인할 뿐 안전성이나 최신성을 증명하지 않는다.

`runtime_guard.py render`가 받는 manifest는 projection 루트의 `SOURCE_MANIFEST.json`이다:

```json
{
  "schema": 1,
  "created_at": "2026-09-11T00:00:00Z",
  "sources": {"app": {"revision": "verified-commit-or-null", "freshness": "verified-or-unknown"}},
  "files": {"app/src/example.py": "64-lowercase-hex-sha256-of-file"}
}
```

`files`는 manifest 자신을 제외한 **모든** 파일의 상대 POSIX 경로와 SHA256이다. Hash는 host가 계산한다. 예시 hash는 실행 가능한 값이 아니다. Manifest와 projection을 모델이 수정할 수 없어야 한다. revision/freshness를 알 수 없으면 unknown으로 보고한다.

Native shell은 source 탐색과 읽기만 한다. DB·로그·외부 자료는 host의 bounded read tools로 제공한다:

- DB는 read-only role/view 또는 엄격한 dataset/query allowlist. SQL 문자열·DSN을 모델이 지정하지 않게 한다.
- 실행 이력·정제 로그·문서 검색은 데이터 범위/행 수/기간/필드 제한을 host가 검증한다. 로그에서 token/PII를 제거한다.
- Source path는 루트 내부로 resolve하고 symlink를 거부한다. 과대한 양의 line/search 범위는 명시된 상한으로 clamp하고 반환값에 실제 범위를 알린다. 기본 예: source120줄, search30건/context120줄. 음수·잘못된 타입·경로 이탈은 거부한다. 선택적 `path_prefix`가 빈 문자열이면 생략한다.
- 첨부는 host가 해당 채널의 권한을 검증해 가져오고 MIME/크기/개수를 제한한다. 파일명·OCR 요약만 전달하지 않는다. **turn input**과 **dynamic tool output**의 이미지 schema는 서로 다를 수 있으므로 실제 설치 schema로 확인하고 원문 이미지와 tool image 모두 해당 native session에 귀속한다.
- 접수/답변은 host workflow다. 모델의 구조화된 결과를 검증한 뒤 목적지·권한·중복 키를 host가 결정한다. 임의 Slack/GitHub write tool이나 배포 도구를 노출하지 않는다.

## Native 설치와 정책

플랫폼에 맞는 **전체 package**를 설치한다. Linux에서 executable만 복사하면 bundled bubblewrap이 없어 sandbox 실행이 실패할 수 있다. 공식 release artifact/version/checksum을 검증·기록한다. Mac의 npm `codex` wrapper는 Node/PATH에 의존하므로 service에는 package 안의 실제 native executable을 사용한다.

Pinned schema를 로컬에서 생성해 실제 필드 이름을 확인한다. CLI help의 `app-server generate-json-schema`를 사용한다. 업그레이드는 schema diff, 아래 lifecycle, OS probe, 실제 대화 acceptance가 모두 통과한 뒤 적용한다.

`runtime_guard.py`의 named `agent-readonly` config를 사용한다. `:root=deny`, `:minimal=read`, 검증한 projection과 **실제 executable 경로**만 read, network off다. exact executable read가 없으면 sandbox helper 재실행이 막힐 수 있다. legacy `sandbox_mode`/`sandboxPolicy`를 이 named profile과 혼합하지 않는다. thread와 turn에도 같은 profile을 명시한다. 승인 요청을 자동 허용하는 fallback은 두지 않는다.

Host app-server에는 모델 통신을 위한 연결이 필요하지만 **모델 shell**에는 네트워크가 없어야 한다. Native state/auth/rollout은 projection 밖 private 디렉터리에 둔다. app-server 환경도 PATH, 격리된 HOME/CODEX_HOME, LANG만 전달하는 allowlist를 기본으로 한다. Shell 환경에는 HOME/CODEX_HOME이나 host 자격증명을 전달하지 않는다. 사용자 shell profile·global skill·plugin·hook discovery는 끈다. Agent instructions는 검토한 자산을 developer instructions로 전달한다.

읽기 전용 runtime에서는 fresh home의 기본값을 믿지 않고 `[features] hooks=false`를 명시한다. helper probe는 native `features list`의 적용된 값도 확인한다.

Linux systemd의 `RestrictAddressFamilies`에는 bubblewrap network namespace 설정에 필요한 **AF_NETLINK**가 필요할 수 있다. 이는 sandbox shell의 외부 네트워크 허용과 다르다. 경계를 넓히기 전에 같은 service identity와 unit 옵션으로 실제 helper 오류를 확인한다. `NoNewPrivileges` 등 기존 제한을 무턱대고 없애지 않는다. MemoryMax/TasksMax는 host에서 실측하고 queue 동시성을 맞춘다. 과거 호스트의 350MiB 같은 수치를 범용 정답으로 고정하지 않는다.

## App-server와 세션

공식 native protocol을 newline JSON-RPC로 연결한다. Host 요청은 생성한 request ID와 진행 중인 tenant/turn에 묶고 알 수 없는 응답/서버 요청은 거부한다. 모델이 arbitrary RPC method/params를 선택하는 도구를 만들지 않는다.

1. `initialize`(experimentalApi capability 포함) → `initialized`.
2. 조직의 선택한 인증을 연결하고 `account/read`로 identity 확인. 계정에서 model/effort 지원 여부를 확인한다. 미지원이면 확인된 대안을 사용자에게 제시하며 조용히 바꾸지 않는다.
3. 신규 대화 `thread/start`: model, cwd, developer instructions, `approvalPolicy: "never"`, `permissions: "agent-readonly"`, host read tool schema를 전달한다. `dynamicTools` 각 항목은 `type: "function"`, name/description/inputSchema를 갖는다.
4. thread ID를 tenant/session registry에 영속 저장한다. 이후 프로세스에서도 `thread/resume`으로 같은 thread를 복원한다. **resume에는 dynamicTools를 다시 넣지 않는다** — 저장된 도구가 복원된다. 도구 계약 변경 시 명시한 session migration/new-session 정책을 적용한다.
5. `turn/start`에 input과 같은 permissions/effort를 명시한다. 기존 turn이 진행 중이면 session lock으로 직렬화한다. 모델 요청은 `item/tool/call`, 인증 갱신 등 설치 schema의 구체적 method allowlist로만 처리한다.
6. tool 결과는 call ID와 현재 tenant에 결속한다. 승인 요청·raw command execution·thread shell RPC는 봇 경로에서 거부한다. `command/exec`는 **운영자 OS probe 전용**이며 runtime RPC allowlist에 넣지 않는다.
7. 최종 응답·usage·상태를 저장한 뒤 host outbox로 같은 대화에 전달한다. 다음 입력은 같은 session으로 이어진다. thread를 못 찾거나 resume이 실패하면 조용히 문맥을 지운 새 세션으로 바꾸지 말고 상태를 알린다.

실제 field/type은 설치 schema가 우선이다. 공식 참고: [Codex app-server](https://developers.openai.com/codex/app-server), [Codex permissions](https://developers.openai.com/codex/security). Version을 바꾸면서 SDK의 유사 필드명을 추측해 사용하지 않는다.

## 응답 의무와 복구

채널 자동 반응은 일상 대화/업무 제보를 구분한다. 이상 상태·불일치·오류 화면은 물음표나 멘션 없이도 제보다. 단순 keyword gate 하나로 native 조사 전에 버리지 않는다. DM과 기존 bot 대화의 후속 질문은 직접 응답 대상으로 취급한다. 기존 접수 분류가 있으면 조사/답변과 접수 여부를 분리한다.

조사 대상으로 선택하거나 실제 읽기를 시작하면 durable `reply_expected`와 근거 있는 activity를 저장한다. 그 이후 최종 `ignore`가 와도 host가 답변/재검토로 전환한다. 성공한 tool read에만 “확인했다”는 진행 메시지를 붙인다. timeout·인증 실패·한도 초과 시 검증한 범위와 다음 확인 대상을 담아 종료 응답을 저장한다.

Queue는 lease heartbeat와 retry/backoff, event/outbox idempotency를 유지한다. 사용 중인 session lock은 nonblocking defer하고 메시지 처리 실패 횟수를 소모하지 않는다. 900초 turn보다 짧은 lease를 heartbeat 없이 사용하지 않는다. 플랫폼의 전달 응답이 유실된 경우 reconciliation 없이 무한 재발송하지 않는다.

Transport는 프레임/이미지/전체 출력 크기 제한, deadline, child stderr 제한을 둔다. 예시 최대 프레임8MiB는 host 정책과 이미지 제한에 맞춘다. interrupt/timeout/예외 때 **자신이 띄운 process group 전체**를 TERM→짧은 wait→KILL로 종료한다. leader 종료만 보고 손자 프로세스를 남기지 않는다. 전체 OS나 다른 봇을 kill하지 않는다.

Upgrade 시 입력을 유실하지 않는 drain/queue 정책과 code/config rollback을 준비한다. 실패 보고 코드가 예외를 내더라도 `finally`에서 복구를 수행한다. 현재 DB에 새 메시지가 들어왔다면 과거 DB backup으로 덮지 않는다. 배포 후 service active뿐 아니라 installed source, native read, 인증/동일 session 재사용, 최종 outbox를 검증한다.
