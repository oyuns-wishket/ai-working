# ai-working

Claude Code와 Codex가 같은 글로벌 규칙, 스킬, hook, workspace 기본값을 읽는 공개 AI SSOT다. 이 저장소 하나가 정본이며 별도 overlay 저장소를 결합하지 않는다.

## 원칙

- 글로벌 에이전트 규칙은 `global/CLAUDE.md`에 쓴다.
- 재사용할 절차는 `skills/<name>/SKILL.md`에 쓴다.
- 공통 hook은 `hooks/`, workspace 기본값은 `workspaces/`에 쓴다.
- `~/.claude`, `~/.codex`, `~/.agents`의 설치 결과를 정본처럼 직접 수정하지 않는다.
- 개발 과정에서 새 규칙이나 스킬이 필요해지면 같은 작업에서 이 저장소를 갱신하고 검증한다.
- 비밀번호, token, 고객 식별자, 내부 URL, 개인 연락처 같은 민감 정보는 커밋하지 않는다. 해당 값은 프로젝트가 승인한 secret store나 machine-local 설정에 둔다.

## 설치

clone이나 bootstrap 전에 사용할 사람이 checkout 위치를 먼저 정한다. 이미 쓰는 개발 폴더가 있으면 그 구조를 우선하고, 선호가 없을 때만 `~/ai-working`을 제안한다. 원작성자의 상위 폴더 이름을 복사하지 않는다.

```bash
AI_WORKING_ROOT="$HOME/ai-working" # 원하는 절대경로로 변경 가능
git clone https://github.com/oyuns-wishket/ai-working.git "$AI_WORKING_ROOT"
cd "$AI_WORKING_ROOT"
./bootstrap.sh --dry-run
./bootstrap.sh
./bootstrap.sh --status
```

bootstrap은 다음을 수행한다.

- `global/CLAUDE.md`를 Claude에 import하고 Codex `AGENTS.md`에 연결
- 모든 `skills/*`를 Claude와 Codex에 개별 symlink로 연결
- workspace 공통 규칙을 구성된 로컬 workspace에 연결
- hook 파일을 설치하고 Claude/Codex hook manifest를 기존 설정에 병합
- 예전 ai-working 계열에서 관리하던 link와 hook wiring을 현재 public 정본으로 교체
- 기존 memory symlink의 내용을 보존한 뒤 machine-local real directory로 전환
- 교체되는 파일을 `~/.claude/backups/ai-working-<timestamp>/`에 백업

다른 경로의 시험용 home에서 검증할 수 있다.

```bash
./bootstrap.sh --target-root /tmp/ai-working-home --dry-run
./bootstrap.sh --target-root /tmp/ai-working-home
./bootstrap.sh --target-root /tmp/ai-working-home --status
```

`--dry-run`은 변경 내용을 보여주며 파일을 바꾸지 않는다. `--status`는 불일치가 있으면 non-zero로 종료한다. 같은 상태에서 bootstrap을 다시 실행하면 변경이 0이어야 한다.

## 업데이트와 여러 머신 동기화

정본을 고친 머신에서 검증하고 commit/push한 뒤 다른 머신에서 실행한다.

```bash
cd "<처음 선택한 ai-working checkout 경로>"
./bootstrap.sh --pull
./bootstrap.sh --status
```

숨은 background 복사는 없다. 각 머신은 같은 public Git 저장소를 pull하고 bootstrap으로 연결 상태를 맞춘다. 로그인, OS 권한, credential은 각 머신에서 따로 관리한다.

## 규칙과 스킬을 추가하는 방법

글로벌 동작을 바꿀 때는 `global/CLAUDE.md`를 수정한다. 특정 반복 작업을 재사용하려면 `skills/<name>/SKILL.md`를 만들고 필요한 script, reference, asset을 그 skill 디렉토리 안에 둔다.

```text
ai-working/
├── global/
│   ├── CLAUDE.md
│   └── governance-hooks.json  # one definition, native runtime adapters
├── hooks/
├── skills/
│   └── <name>/SKILL.md
├── workspaces/
├── templates/
├── tests/
├── manifest.json
└── bootstrap.sh
```

변경 후 최소 검증:

```bash
python3 scripts/public_audit.py --history
python3 scripts/validate_skills.py
bash -n bootstrap.sh hooks/*.sh
node --test tests/*.test.mjs
./bootstrap.sh --target-root "$(mktemp -d)" --dry-run
```

공개 코드에서 막아야 하지만 그 값 자체도 공개하면 안 되는 개인명·고객명은
`~/.config/ai-working/public-audit-denylist.txt`에 한 줄에 하나씩 둔다. CI에는 같은 내용을 base64로 인코딩한
`AI_WORKING_AUDIT_DENYLIST_B64` repository secret을 설정한다. 감사기는 이 목록을 출력하지 않는다.

Skill은 Agent Skills 표준 frontmatter의 `name`, `description`을 포함해야 한다. Claude 전용 도구명이 필요하면 의도를 먼저 쓰고 Codex에서 대응되는 native 기능을 사용하도록 설명한다.

현재 포함된 26개 skill은 다음 영역을 다룬다.

| 영역 | Skill |
|---|---|
| SSOT·환경 | `agent-environment`, `claude-setup`, `personal-ai-ssot`, `ssotify`, `sync-consortium` |
| 개발 흐름 | `design-workflow`, `dev-protocol`, `feature-flow`, `multi-agent-dev`, `paseo-setup` |
| 기획·검증 | `dev-review-deck`, `gen-spec`, `generate-spec`, `knowns`, `wiki-curator` |
| 에이전트·연동 | `agent-bot-setup`, `external-consumer-sync`, `hermes-bot-setup`, `knowledge-wiki`, `online-channel-guide` |
| 인프라·원격 | `customer-infra-ops`, `mac-file-sync`, `project-wiki-context`, `remote-setup`, `remote-ssh-edit` |
| 개인 업무 | `calendar` |

## 개인화

다른 사람이 이 저장소를 자기 AI SSOT로 사용할 때는 bootstrap보다 먼저 `personal-ai-ssot` skill로 인터뷰한다. 사용하는 장비, AI 도구, checkout 위치, 폴더와 파일 이름, 업무 흐름을 정한 다음 fork 또는 새 정본을 그 위치에 만들고 연결한다.

```text
skills/personal-ai-ssot/SKILL.md를 읽고 한 번에 한 질문씩 인터뷰해서
이 fork를 내 AI SSOT로 개인화해줘. 연결 전에 dry-run 결과를 보여줘.
```

한 대의 Mac과 한 AI 도구만 써도 된다. 선택하지 않은 원격 접속, 회사 연동, 외부 서비스는 설치하지 않는다.

## Hook

| 파일 | 역할 |
|---|---|
| `block-dangerous.sh` | 위험한 shell 명령 차단 |
| `preview-db-guard.mjs` | 보호 branch와 production DB 오접속 방지 |
| `dev-resource-guard.mjs` | local DB/Docker 자원 점검과 세션 소유 자원 정리 |
| `pre-tool.sh` | 승인 범위를 검증한 DB 변경의 실행 표시 확인 |
| `session-entry.mjs` | Git 정보와 최대 8 KiB HANDOFF를 한 번 제공 |
| `handoff-sync.sh` | 비활성 호환 진입점; 파일 수정·commit·push 없음 |

매 편집 lint·문서 알림은 기본 등록에서 제외한다. 필요한 검증은 작업 완료 시 실행한다. 열린 이슈·디스크 시작 조회는 각각 `AI_WORKING_STARTUP_ISSUES=1`, `AI_WORKING_STARTUP_DISK=1`로 선택한다.

Hook 설정은 기존 Claude/Codex 설정 전체를 덮지 않는다. ai-working이 관리하는 hook command만 현재 manifest로 교체하고 다른 도구의 hook은 보존한다.

설치 연결과 실제 동작 점검은 구분한다. [Hook 동작·복수 workspace 설정](docs/hook-behavior.md)에서
로컬 설정과 회귀 검증 절차를 확인한다. [작업별 측정](docs/task-metrics.md)은 명시적으로 연결한 세션의
사용량·시간·검증 결과를 machine-local 상태로 기록한다.

## 필요한 도구

- `git`
- `node`, `python3`, `jq`
- macOS 또는 Linux의 표준 shell 도구

각 skill이 요구하는 선택 도구는 해당 `SKILL.md`에 적는다.

## 라이선스

이 저장소는 [MIT License](LICENSE)로 공개한다. fork와 개인화, 수정, 재배포가 가능하다.

## 되돌리기

변경 전 파일은 `~/.claude/backups/`에 보존된다. 설치 연결을 해제할 때는 먼저 `./bootstrap.sh --status`로 현재 대상을 확인하고 필요한 symlink/import/hook만 제거하거나 백업을 복원한다. machine-local memory 디렉토리는 자동 삭제하지 않는다.
