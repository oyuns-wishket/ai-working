# Session runners — 플랫폼별 실행 규칙

확인 기준: Claude Code 2.1.266, Codex CLI 0.153.4 (2026-09-15). 플래그가 바뀌면 `session_runner.py`의 `claude_command`/`codex_command`와 이 문서를 함께 갱신한다.

## 목차

1. 공통
2. Claude 세션
3. Codex 세션
4. subagent 모드 (in-process)
5. hook·환경변수
6. 세션 로그와 측정

## 1. 공통

- 프롬프트는 `assets/lane-prompt.md`를 렌더해 stdin으로 전달한다. 인자 길이 제한을 피하고 로그에 프롬프트가 남지 않게 한다. 렌더 결과는 `<state>/tasks/<repo-id>/<task>/<lane>/attempt-N/prompt.md`에 보존된다.
- 결과는 `assets/lane-result.schema.json`으로 강제한다. 스키마는 `additionalProperties: false`이고 모든 키가 `required`다. Codex(OpenAI strict mode)가 이를 요구하며 Claude도 같은 파일을 받는다.
- 각 세션은 `start_new_session=True`로 자체 process group을 가진다. `cancel`은 group 전체에 SIGTERM → 10초 후 SIGKILL을 보낸다. `run`은 SIGINT/SIGTERM을 받으면 실행 중인 lane을 모두 취소한 뒤 종료한다.
- `--bare`(Claude)나 `--ignore-rules`(Codex)는 쓰지 않는다. 프로젝트 규칙과 hook이 lane에도 적용되어야 한다.

## 2. Claude 세션

```text
claude -p --output-format json --json-schema <schema-json>
       --permission-mode bypassPermissions --permission-prompts none
       --session-id <uuid> --name msd-<task>-<lane>
       [--model <m>] [--effort <e>] [--max-budget-usd <n>]
       --disallowedTools <list>
```

| lane | disallowedTools |
|---|---|
| write | `Bash(git push*)` + plan의 `disallowed_tools` |
| read | `Write,Edit,MultiEdit,NotebookEdit,Bash(git push*),Bash(git commit*)` + plan의 `disallowed_tools` |

- `--permission-prompts none`은 prompt가 뜰 상황을 자동 거부로 바꾼다. lane이 `blocked`/`failed`로 끝나면 결과의 `permission_denials`를 먼저 본다.
- 결과 JSON의 `structured_output`이 lane result다. `session_id`, `total_cost_usd`, `permission_denials`, `usage`도 상태에 기록된다.
- 재시도: `--resume <session_id>`로 같은 대화를 이어간다. 새 시도는 `--session-id`를 새로 발급한다.
- 실제 명령 확인 방법: 프로브에서 `env -u CLAUDECODE` 없이도 `-p`가 동작했다. runner는 안전을 위해 세션 식별 환경변수를 제거한다(§5).

## 3. Codex 세션

```text
codex exec [resume <thread_id>] -C <cwd> -s <workspace-write|read-only>
           --json -o <last-message.json> --output-schema <schema-file>
           [-m <model>] -c model_reasoning_effort="<effort>" -
```

- 마지막 인자 `-`가 stdin 프롬프트를 의미한다. 없으면 "Reading additional input from stdin..."으로 인자와 stdin이 합쳐진다.
- `exec`는 비대화형이라 approval prompt가 없다. sandbox가 유일한 경계이므로 write lane은 `workspace-write`, read lane은 `read-only`다. `--dangerously-bypass-approvals-and-sandbox`는 쓰지 않는다. 글로벌 규칙: 도구 차이로 제한을 완화하지 않는다.
- `--json` 이벤트 스트림에서 `thread.started.thread_id`, `turn.completed.usage`, `error`/`turn.failed`를 읽는다. lane result는 `-o` 파일에서 읽는다.
- 기본 effort는 `high`. 고위험 리뷰는 plan에서 `xhigh`를 지정한다.
- `codex exec resume <thread_id>`의 옵션 호환은 실측으로 확인한 범위만 신뢰한다. 실패하면 `--follow-up`으로 새 세션을 만든다.

## 4. subagent 모드 (in-process)

읽기 전용 fan-out은 세션을 띄우지 않고 플랫폼 native subagent로 처리한다. 교차 플랫폼이 되지 않지만 읽기 전용이므로 필요 없다.

- Claude: `Explore`(경계 있는 탐색) 또는 `general-purpose`(독립 검증). 프로젝트 `.claude/agents/*.md`가 더 구체적이면 우선한다.
- Codex: built-in `explorer`, `worker`, `default` 또는 프로젝트 `.codex/agents/*.toml`.
- subagent lane도 plan에 `mode: subagent`, `write: false`로 기록해 계획 표에 나타나게 한다. `session_runner.py`는 subagent lane을 실행하지 않는다.
- subagent에게 쓰기를 주지 않는다. 쓰기는 항상 session lane이다.
- subagent가 중첩 spawn하지 않게 한다.

## 5. hook·환경변수

runner가 lane 환경에 적용하는 것:

| 변수 | 값 | 이유 |
|---|---|---|
| `MULTI_SESSION_DEV_LANE` | `<task>/<lane>` | 중첩 spawn 차단. runner는 이 변수가 있으면 `run`/`spawn`을 거부한다 |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | `0` | named subagent가 teammate로 승격되어 이중 오케스트레이션이 되는 것을 막는다 |
| 제거 | `CLAUDECODE`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_CHILD_SESSION`, `CLAUDE_CODE_MESSAGING_*`, `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_PID`, `CLAUDE_EFFORT` | Lead 세션의 식별자가 lane에 상속되지 않게 한다 |

hook: lane 세션도 글로벌 `SessionStart`/`PreToolUse` 등 hook을 그대로 실행한다. hook이 stdin/prompt를 요구하면 lane이 멈추므로 hook은 비대화형이어야 한다. Codex hook trust는 `scripts/codex_hook_trust.py`가 관리하는 값을 그대로 사용한다.

## 6. 세션 로그와 측정

runner는 lane 종료 시 transcript 경로를 찾아 `session_log`에 기록한다.

- Claude: `~/.claude/projects/<cwd-slug>/<session_id>.jsonl`. slug는 cwd의 `/`와 `.`을 `-`로 바꾼 값. 없으면 전체 project 디렉토리에서 session id로 검색.
- Codex: `~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<thread_id>.jsonl`.

작업 측정을 쓰는 경우 이 경로를 `task_metrics.py add-session --session-log <platform>:<path>`에 넘긴다. 경로가 `null`이면 usage는 unknown으로 두고 계속한다.
