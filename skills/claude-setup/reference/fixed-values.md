# claude-setup — 경로 계약

| 항목 | 값 |
|---|---|
| ai-working repo | `$AI_WORKING_ROOT` (정책·스킬·hooks·templates·workspace·bootstrap의 유일한 Git SSOT) |
| 동기화 | `"$AI_WORKING_ROOT/bootstrap.sh" --pull` + `/sync-consortium` |
| machine-local 설치 대상 | `~/.claude/hooks/*` — 소스는 ai-working 루트 `hooks/` |
| OMC 파일 | `~/.claude/CLAUDE.md` — OMC 소유, 건드리지 않음 |
| 의존성 | `jq`, `gh`(+`gh auth login`), `coreutils`(gtimeout) |
| 프로젝트 경로 | manifest나 프로젝트 규칙에서 지정하며 `$HOME` 기준 경로 사용 |

## hook 와이어링
| 이벤트 | 기존 | 거버넌스 추가 |
|---|---|---|
| SessionStart | `session-context.sh` (git/node 정보) | `session-start.sh` (열린이슈 R3·handoff·디스크 R9) |
| PreToolUse(Bash) | `block-dangerous.sh` (rm-rf/DROP(DB컨텍스트)/force-push **deny**) | `pre-tool.sh` (마이그 `supabase db push` **deny+dry-run+CONFIRMED escape** R1) |
| PostToolUse(Edit\|Write) | `post-edit-context.sh` (로컬 tsc/ruff lint, JSON 도달) | `post-tool.sh` (ERP 도메인 R7·인프라파일 R12·TODO(issue) R2) |
| 공통 | — | `lib.sh` (run_guarded 타임아웃·git 헬퍼) |

> per-hook `timeout`은 settings.json에 있음(gtimeout 부재 시에도 Claude Code가 강제 종료).
