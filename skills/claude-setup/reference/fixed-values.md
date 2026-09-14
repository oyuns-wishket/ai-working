# claude-setup — 경로 계약

| 항목 | 값 |
|---|---|
| ai-working repo | `$AI_WORKING_ROOT` (정책·스킬·hooks·templates·workspace·bootstrap의 유일한 Git SSOT) |
| 동기화 | `"$AI_WORKING_ROOT/bootstrap.sh" --pull` + `/sync-consortium` |
| machine-local 설치 대상 | `~/.claude/hooks/*` — 소스는 ai-working 루트 `hooks/` |
| OMC 파일 | `~/.claude/CLAUDE.md` — 공통 정본 import; lean profile은 오래된 OMC 자동 안내를 백업 후 제거 |
| 의존성 | `jq`, `gh`(+`gh auth login`), `coreutils`(gtimeout) |
| 프로젝트 경로 | manifest나 프로젝트 규칙에서 지정하며 `$HOME` 기준 경로 사용 |

## Hook wiring

The canonical definition is `global/governance-hooks.json`. Bootstrap translates native Codex event fields; do not maintain a second policy manifest.

| Event | Shared behavior |
|---|---|
| SessionStart | `session-entry.mjs`: bounded Git/handoff context |
| UserPromptSubmit | resource and configured Preview DB checks |
| PreToolUse(Bash) | dangerous-command/migration guards and resource checks |
| PreToolUse(Bash / file edits) | configured Preview DB policy |
| PostToolUse(Bash) | confirm attributable resource ownership |
| SessionEnd | detach cleanup of proven session-owned resources |

No automatic HANDOFF writes, commits or pushes; no default per-edit lint/reminder. Native Codex hooks need exact-definition trust after manifest changes. See `docs/hook-behavior.md`; installation status alone does not establish runtime readiness.
