# Local config and Worker spec

## 목차

1. Machine-local config
2. Project Worker spec
3. Adapter rendering

## 1. Machine-local config

기본 위치는 `~/.config/multi-session-dev/config.json`이다. 절대경로는 이 파일에만 저장하고 Git에 commit하지 않는다.

```json
{
  "schema_version": 1,
  "workspace_roots": [
    "/Users/example/projects"
  ],
  "erp_domain_references": [
    "/Users/example/projects/erp-domain.md"
  ],
  "worktree_root": "/Users/example/.worktrees",
  "platforms": [
    "claude",
    "codex"
  ]
}
```

- `workspace_roots`: optional. 현재 repo가 등록 root 밖이어도 사용자가 명시적으로 요청하면 허용하되 보고한다.
- `erp_domain_references`: optional. 존재하는 file만 사용한다.
- `worktree_root`: write Worker를 쓸 때 required.
- `platforms`: `claude`, `codex` 중 하나 이상.

## 2. Project Worker spec

정본은 `<repo>/.agents/multi-session-dev/workers/<name>.json`이다.

```json
{
  "schema_version": 1,
  "name": "erp-domain-analyst",
  "description": "ERP 업무 흐름과 데이터 불변조건을 분석하는 read-only Worker",
  "capability": "erp-domain-analyst",
  "write_access": false,
  "command_access": false,
  "codex_reasoning_effort": "high",
  "instructions": "현재 repo의 CLAUDE.md와 AGENTS.md를 먼저 읽는다. ...",
  "required_references": [
    "CLAUDE.md",
    "AGENTS.md"
  ]
}
```

필수:

- `schema_version`: `1`
- `name`: lowercase kebab-case
- `description`: trigger와 역할을 설명
- `capability`: `worker-capabilities.md`의 역량 또는 프로젝트 고유 역량
- `write_access`: boolean
- `instructions`: 역할 경계, 작업 절차, 반환 evidence

선택:

- `command_access`: read-only Worker에게 검증용 Bash를 제공할지 여부. 기본 `false`.
- `codex_reasoning_effort`: `low|medium|high|xhigh|max|ultra`
- `required_references`: repo-relative path 목록

spec에 secret, 개인 절대경로, 특정 세션 task를 넣지 않는다.

## 3. Adapter rendering

`render_worker.py`는 정본 spec으로 다음을 생성한다.

- Claude: `.claude/agents/<name>.md`
- Codex: `.codex/agents/<name>.toml`

read-only spec:

- Claude: Write/Edit를 제공하지 않는다.
- Codex: `sandbox_mode = "read-only"`.

write spec:

- Claude: Read/Write/Edit/Bash/Grep/Glob을 제공한다.
- Codex: `sandbox_mode = "workspace-write"`.

기존 adapter가 있으면 renderer는 기본적으로 실패한다. `--force`는 사용자가 해당 diff를 승인한 경우에만 사용한다.
