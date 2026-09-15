# 2026-09-15 multi-session-dev skill

Lead 세션이 여러 CLI 세션(Claude, Codex)을 lane별 worktree에서 병렬 실행하고 통합하는 스킬. `multi-agent-dev`를 흡수한다. `dev-protocol → multi-session-dev` 단방향 계약.

## 목표 / 확정 사항

- 한 스킬, 두 실행 모드. 읽기 전용 fan-out은 in-process subagent, 쓰기 lane과 리뷰는 별도 세션(`claude -p`, `codex exec`).
- 쓰기 lane은 항상 세션 + 전용 worktree. in-process 쓰기 subagent는 두지 않는다.
- Lead 플랫폼과 무관하게 같은 runner가 Claude·Codex 세션을 모두 띄운다.
- lane branch는 Lead task branch에 순차 merge. develop/main 반영·push·배포는 스킬 범위 밖이며 호출자(`dev-protocol`)가 소유한다.
- worktree 정리는 세션 종료가 아니라 통합·검증 완료 후. 실패 lane worktree는 사람 결정까지 보존.
- 새 스킬은 `dev-protocol` 절을 참조하지 않는다. 입력·출력 계약으로만 연결하고, 입력에 없는 승인은 `blocked`로 반환한다.

## Gate evidence

- 사용자 요청: 세션 오케스트레이션 스킬 개발 계획. 흡수 방식·모드 구분·정리 시점·플랫폼 대칭을 대화에서 확인함.
- 확인 질문: 없음. 흡수(`multi-agent-dev` 퇴역)는 권장안으로 제시했고 사용자가 이견 없이 진행을 지시함.
- 승인된 범위: 이 계획 문서 작성. 구현·commit·push는 별도 지시("ㄱㄱ" 등)로 시작한다.
- 미승인 가정: 없음.

## Issue tracking

- 대표: 생략. 개인 SSOT 저장소의 스킬 개발이며 외부 이슈 트래커 연결 대상 없음.
- 완료 시점: 구현 + 검증 + commit/push + 다른 장비 bootstrap.

## 조사 근거 (2026-09-15)

| 출처 | 확인 사실 | 반영 |
|---|---|---|
| Claude Code agent-teams 공식 문서 | 실험적, Claude 전용, interactive 전용, `-p`에서 teammate 미생성, teammate별 worktree 없음 | teams 미사용. `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 켜지 않음(이중 오케스트레이션 방지) |
| Anthropic multi-agent research 포스트 | 멀티에이전트 토큰 약 15배. 코딩은 research보다 병렬화 여지가 적음 | 세션 모드는 독립 쓰기 lane에 한정. 실행 여부 판단 절을 엄격히 |
| 33,596 agent PR 충돌 연구 | 교차 에이전트 conflict 41.7%, 파일 집합 비중복 시 0 근접. 순차 merge + rebase 권장 | `lane_plan.py` 소유권 중복은 실패. `integrate.py`는 순차 merge, 사전 `git merge-tree` |
| Cross-model review 논문 (arXiv 2607.21656) | Claude→Codex 리뷰 +18.1pp, Codex→Claude 리뷰 −8.6pp (LeetCode 116문제, 실행 없음) | gate 리뷰어 기본 Claude. Codex 리뷰는 advisory(비차단). 논문의 일반화 한계를 reference에 명시 |
| 실무 보고 (10+ agents, Willison 등) | 3~5 lane 상한, 병목은 사람 리뷰·주의력. worktree는 DB·포트·credential 미격리 | 동시 상한 기본 3. 구조화 상태 표. lane 프롬프트에 자원 사용 제한 명문화 |
| Codex CLI 문서 | `agents.max_threads` 기본 6, `codex exec --json -o --output-schema` | Codex lane 실행 명령 확정 |
| OpenAI `codex-plugin-cc` | Claude→Codex 단방향 wrapper, worktree·병렬 없음 | 의존하지 않음. runner가 `codex exec`를 직접 호출 |

## 결정

| 항목 | 결정 | 근거 |
|---|---|---|
| 스킬 이름 | `multi-session-dev` | `multi-agent-dev`와 구분되고 세션 단위 실행을 드러냄 |
| 흡수 vs 병존 | 흡수, `multi-agent-dev` 디렉토리 제거 | ssotify "현재 소유자 확장", 트리거 중복 방지 |
| worktree 생성 주체 | runner가 lane spawn 시 `worktree_manager`로 생성 | Codex에 `-w` 없음. 상태 추적·안전 cleanup 재사용 |
| Claude 쓰기 세션 | `command claude -p --output-format json --json-schema <schema> --permission-mode bypassPermissions --permission-prompts none --disallowedTools "Bash(git push*)" ... --session-id <uuid> --name <lane> --model --effort --max-budget-usd` | 무인 실행에서 prompt는 자동 거부. push·외부 write는 도구 수준에서 차단 |
| Claude 읽기 세션 | 위와 같되 `--disallowedTools Write,Edit,MultiEdit,NotebookEdit,Bash(git push*),Bash(git commit*)` | Bash 검증 명령은 허용해야 하므로 deny 목록 방식 |
| Codex 쓰기 세션 | `codex exec -C <worktree> -s workspace-write -m <model> -c model_reasoning_effort=<e> --json -o <file> --output-schema <schema> -` (stdin 프롬프트; `exec`는 approval 없음) | 글로벌 규칙: 도구 차이로 제한 완화 금지. bypass 미사용 |
| Codex 읽기 세션 | `-s read-only` | |
| `--bare` | 사용 안 함 | 프로젝트 규칙·hook 로드가 필요 |
| 중첩 spawn | 환경변수 `MULTI_SESSION_DEV_LANE=<task>/<lane>`을 세션에 주입, runner가 설정 시 spawn 거부 | Anthropic가 보고한 재귀 spawn 비용 폭증 방지 |
| 프로세스 관리 | lane마다 자체 process group(`start_new_session`). `cancel`은 group에 SIGTERM→SIGKILL, blocking `run`은 SIGINT/SIGTERM 시 실행 중 lane을 모두 취소 | lane 단위 취소와 Lead 중단 시 정리를 둘 다 만족. 비blocking `spawn`은 고아 가능성이 있어 `run`을 기본으로 문서화 |
| 동시 상한 | 기본 3, config `max_parallel` | 계정 회전 Claude 3·Codex 2, 리뷰 병목 |
| 리뷰 | gate 리뷰어 Claude(구현자와 다른 세션). Codex adversarial review는 advisory | 논문 근거 |
| 재시도 | FAIL lane은 같은 worktree에서 `--resume` / `codex exec resume`으로 이어서. 횟수는 config 기본 3 | 고정 횟수를 스킬 규칙으로 못박지 않음(ssotify) |
| 정리 | 통합·검증 후 clean + merged worktree만 제거. 실패·dirty·미병합은 보존 보고 | 기존 cleanup 의미 유지 |
| 자원 | lane은 Lead가 지정한 DB/Docker만 사용. 새 stack 금지 | 글로벌 규칙(한 stack), worktree 미격리 |
| 측정 | Claude `--session-id`로 JSONL 경로 확정, Codex `--json`의 thread id로 로그 위치 확정 → `task_metrics.py add-session` 후보로 출력 | 실측 smoke에서 경로 확인 후 확정 |

## 파일 계획

```text
skills/multi-session-dev/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── lane-contract.md        # 입력·출력 계약, lane 상태 전이, blocked 규칙
│   ├── session-runners.md      # 플랫폼별 명령·flag·sandbox·hook 동작 (CLI 버전 명시)
│   ├── orchestration.md        # 모드 선택, wave 실행, 모델 라우팅 기본값, merge·충돌·재시도, 리뷰 정책과 근거
│   ├── worker-capabilities.md  # 이동
│   └── schemas.md              # 이동 + config 키 추가
├── scripts/
│   ├── configure.py            # 이동 + max_parallel, role_defaults{platform,model,effort}, max_budget_usd, retry_limit
│   ├── inspect_project.py      # 이동
│   ├── render_worker.py        # 이동
│   ├── worktree_manager.py     # 이동, state root 이름 변경
│   ├── lane_plan.py            # 신규: validate (소유권 중복→실패, DAG 순환, 쓰기 lane worktree 필수, slot 계산→wave)
│   ├── session_runner.py       # 신규: spawn/status/wait/collect/cancel
│   └── integrate.py            # 신규: merge-tree dry-run → 순차 merge → 검증 명령 실행 → 결과 JSON
├── assets/
│   ├── lane-plan.schema.json
│   ├── lane-result.schema.json # STATUS/SCOPE/FILES/EVIDENCE/RISKS/HANDOFF + branch, head_sha, session_log
│   ├── lane-plan.example.json
│   └── lane-prompt.md          # 세션 프롬프트 템플릿
└── tests/
    ├── test_scripts.py         # 이동
    ├── test_lane_plan.py
    ├── test_session_runner.py  # fake claude/codex 실행 파일로 명령 조립·상태·cancel 검증
    └── test_integrate.py       # 임시 git repo로 merge·충돌 보고 검증
```

호출자 갱신:

- `global/CLAUDE.md` 작업 순서 표: `multi-agent-dev` → `multi-session-dev`
- `skills/dev-protocol/SKILL.md` §0: "독립적인 병렬 lane에는 `multi-session-dev`를 추가한다" + 입력 계약 전달 한 줄
- `README.md` 스킬 목록, `docs/skill-consolidation.md` 표에 `multi-agent-dev → multi-session-dev` 행
- `skills/multi-agent-dev/` 삭제, 설치 링크는 bootstrap dry-run으로 확인 후 제거

## 계획

### Phase 1. 계약과 스키마

1. `lane-contract.md`: 입력(승인된 write 범위, 이슈·수용 기준, 검증 명령, commit 허용, 배포 범위), 출력(통합 branch·sha, lane별 결과, 남은 worktree, 위험, 이탈, blocked 사유).
2. `lane-plan.schema.json`, `lane-result.schema.json`, example.
3. `lane-prompt.md`: repo·worktree 절대경로, 허용 파일, 금지 작업, 읽을 규칙, 검증 명령, 자원 제한, 반환 형식, 중첩 spawn 금지.

### Phase 2. 스크립트

1. 기존 4개 이동, state root·prefix 이름 변경, 기존 테스트 통과 확인.
2. `lane_plan.py validate --plan <json> --json`: 실패 조건과 wave 배열 출력.
3. `session_runner.py`
   - `spawn --plan <json> --lane <id>`: worktree 생성(쓰기 lane), 명령 조립, `Popen`(process group), 상태 파일·로그 경로 반환.
   - `status --task <slug>`: lane별 상태 표(text) / JSON.
   - `wait --task <slug> [--lane]`: 종료 대기, 결과 JSON 수집·스키마 검증.
   - `cancel --task <slug> [--lane]`: process group 종료, worktree 보존.
   - 환경변수 guard, `max_parallel` 대기열.
4. `integrate.py --task <slug> --target <branch> --verify "<cmd>"...`: lane별 `git merge-tree` → 충돌 없는 lane부터 순차 merge → 충돌 lane 보고(자동 해결 없음) → 검증 명령 실행 → 결과 JSON.
5. 테스트 3개 신규. fake 실행 파일은 tests 디렉토리 안에 둔다.

### Phase 3. SKILL.md·references·호출자

1. `SKILL.md`: 실행 여부 판단 → 모드 선택 → lane 계획 표(모드 열 포함) 사용자 제시 → wave 실행 → 통합·리뷰 → 출력 계약 반환 → 정리. 승인 문구는 "입력 계약 밖은 blocked" 한 줄.
2. `session-runners.md`, `orchestration.md` 작성. 리뷰 정책 근거와 논문 한계 명시.
3. `agents/openai.yaml` 갱신.
4. 호출자 4곳 갱신, `multi-agent-dev` 제거.

### Phase 4. 검증

1. 정적: `python3 scripts/validate_skills.py`, `python3 scripts/public_audit.py --history`, `python3 -m pytest skills/multi-session-dev/tests`, 기존 hook·bootstrap 테스트.
2. `./bootstrap.sh --dry-run` → 링크 변경이 `multi-agent-dev` 제거 + `multi-session-dev` 추가뿐인지 확인 → 적용 → `--status`.
3. 실측 smoke (임시 git repo, `/tmp`):
   - Claude 쓰기 lane 1 + Codex 쓰기 lane 1 동시 spawn → 각 worktree 파일 수정·commit → 결과 JSON 스키마 통과.
   - Claude 읽기 리뷰 lane → PASS/FAIL 반환.
   - `integrate.py` 순차 merge → 검증 명령 실행 → cleanup → worktree 0.
   - 고의 충돌 케이스: 같은 파일을 두 lane에 배정 → `lane_plan.py` 실패. plan 우회 후 `integrate.py`가 충돌 보고하고 worktree 보존.
   - `cancel` 후 프로세스 잔존 0.
   - 중첩 spawn guard 동작.
4. hook 확인: `-p` 세션에서 `session-start`, `dev-resource-guard`가 prompt 없이 통과. Codex hook trust 유효.
5. 세션 로그 경로 실측 후 측정 절 확정.

### Phase 5. 반영

- 개인 동기화 저장소이므로 main 직접 commit 허용. 검증 결과와 함께 commit·push.
- 다른 장비: `./bootstrap.sh --pull && ./bootstrap.sh --status`.
- HANDOFF 갱신 대상 없음(저장소에 HANDOFF 없음). 이 노트의 Verification 절을 갱신.

## 판단 근거

- 세션 모드를 쓰기 lane으로 한정한 이유: 세션은 규칙·hook·skill을 재로드해 비용이 크고, 읽기 fan-out은 native subagent가 충분하다.
- in-process 쓰기 subagent를 없앤 이유: 파일 범위 제한이 프롬프트 지시에만 의존하고, 다른 플랫폼 리뷰어를 붙일 수 없다.
- agent teams를 대체재로 채택하지 않은 이유: Claude 전용·interactive 전용·worktree 미지원·실험적. 조건이 바뀌면 subagent 모드 대체 후보로 재검토.

## ⚠️ DEVIATION

- ⚠️ Claude `--json-schema`가 `$schema` 메타 키를 거부함(`no schema with key or ref ...2020-12/schema`) → 대응: 자산 파일에서 `$schema` 제거, runner가 Claude에 넘길 때 방어적으로 한 번 더 제거. Codex는 같은 파일을 `--output-schema`로 그대로 사용 → 리뷰: smoke 재실행으로 자체 확인.
- ⚠️ `integrate.py`가 아직 실행되지 않은 lane(plan에는 있으나 state에 없음)에서 KeyError → 대응: `.get()`으로 완화, `test_integrate.py`의 plan에 미실행 review lane을 추가해 회귀 고정 → 리뷰: 자체 확인.
- ⚠️ `platform-adapters.md`는 별도 갱신 대신 삭제하고 subagent 모드 절을 `session-runners.md` §4로 흡수 → 근거: 승인 경계 절이 `dev-protocol`을 역참조하고 있어 단방향 계약과 충돌.

## 다음에 참고

- 리뷰어 플랫폼 휴리스틱은 논문 한 편(LeetCode)에 근거한다. 실제 repo에서 Codex advisory 리뷰가 유효한 반론을 내는 비율을 몇 번 관찰한 뒤 기본값을 재평가한다.
- `--permission-prompts none`은 prompt를 자동 거부하므로 lane이 `blocked`로 끝나는 원인 1순위다. 로그에서 거부된 도구를 먼저 본다.

## Verification (2026-09-15)

- 정적: `validate_skills.py` 24 skills 통과. `public_audit.py --history` 219 tracked files 통과.
- 단위: `skills/multi-session-dev/tests` 27 tests OK (lane_plan 8, session_runner 11, integrate 3, 이동한 기존 5). fake `claude`/`codex` 실행 파일로 명령 조립·worktree·상태·cancel·중첩 guard·retry 검증.
- 저장소: Python 테스트 6개 파일 OK, `node --test tests/*.test.mjs` 34 pass 0 fail (첫 실행 1 fail은 bootstrap 적용과 동시 실행된 영향, 재실행에서 재현 안 됨).
- bootstrap: dry-run이 `claude/codex multi-session-dev` 링크 추가와 `multi-agent-dev` 링크 제거 4건만 보고. 적용 후 `--status` 정상 70개. `~/.claude/skills`, `~/.agents/skills` 모두 새 스킬로 resolve.
- 실측 smoke (`/tmp/msd-smoke`, 실제 CLI):
  - wave 0: Claude sonnet 쓰기 lane + Codex 쓰기 lane 동시 실행 → 각 worktree에서 파일 생성·commit, 결과 JSON 스키마 통과, Lead checkout 무변경. Claude lane 1차 시도는 `$schema` 문제로 실패 후 수정, `run --lane api`로 재시도(attempts=2).
  - 세션 로그 자동 탐지: Claude `~/.claude/projects/-private-tmp-msd-smoke-worktrees-repo-smoke-api/<id>.jsonl`, Codex `~/.codex/sessions/2026/09/15/rollout-*-<thread>.jsonl` 모두 실제 경로 확인.
  - `integrate.py --dry-run` → 실제 merge 2건(`--no-ff`) → verify 2건 exit 0. 통합 후 dirty 0.
  - wave 1: Claude gate 리뷰 PASS, Codex advisory 리뷰 PASS. 둘 다 Lead checkout에서 read-only로 실행, 수정 없음.
  - cleanup: clean + merged worktree 2개 제거, preserved 0. `status`가 task 목록과 lane 표를 정상 출력.
  - hook: `-p` 세션에서 글로벌 SessionStart/PreToolUse hook이 prompt 없이 통과(lane이 정상 종료). Codex lane은 글로벌 규칙과 `dev-protocol` 문서를 스스로 읽음.
- 미실측: `codex exec resume <thread_id>` 옵션 호환. 문서에 "실측 범위만 신뢰, 실패 시 `--follow-up` 새 세션" 명시.
- 비용: smoke 전체 Claude 약 $0.6 (sonnet, 3 세션). Codex는 구독 계정이라 cost 미보고.

## Follow-up (2026-09-15): Codex Lead 실측과 문구 정리

- 사용자 요청: Codex를 Lead로 한 스모크 테스트, 이후 Codex Lead 조건 문서화와 계획 표 확인 문구 정리를 SSOT에 반영.
- 실측 결과 (macOS, Codex CLI 0.153.4, 비대화형, Claude 쓰기 lane + Codex 쓰기 lane):
  - `workspace-write` 기본: worktree 생성 실패. `.git` 읽기 전용 보호.
  - `.git` writable_roots + network_access: Claude lane 완료, Codex lane은 `~/.codex` 쓰기 불가로 시작 실패.
  - 위 + `~/.codex` writable: Codex lane `blocked`, `sandbox-exec: sandbox_apply: Operation not permitted`. 중첩 sandbox 불가.
  - `danger-full-access`: 두 lane 완료, 병합 2건, 검증, cleanup 완료. Lead 요약이 아니라 git log·파일·worktree·lane 상태로 직접 확인.
- 반영: `session-runners.md` §7 Lead 플랫폼 조건, `SKILL.md` 개요와 트러블슈팅 3행.
- 계획 표 문구: "마지막 확인점"은 이미 승인한 범위를 다시 묻게 만들 수 있어, 승인 범위 안이면 바로 실행하고 범위 밖 차이만 확인하도록 수정.
- 미실측: Codex sandbox 환경변수로 Lead 상태를 판별하는 방법. 실측 시점에 Codex API가 429를 반환해 확인하지 못했고, 문서에는 실제 관찰한 오류 문구만 판별 기준으로 적었다.
- 범위 밖으로 남긴 것: 전역 규칙 표의 "독립 lane 둘 이상·다중 모듈·DB/권한/migration/연동 작업" 나열 문구. 사용자 요청 범위가 아니어서 수정하지 않았다.
