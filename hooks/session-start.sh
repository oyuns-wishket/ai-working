#!/bin/sh
hook_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
. "$hook_dir/lib.sh"
payload="$(cat)"
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null)"
[ -n "$cwd" ] && cd "$cwd" 2>/dev/null
out=""
# Rule 3 — open issues (read-only)
if [ "${AI_WORKING_STARTUP_ISSUES:-0}" = 1 ] && in_git_repo && has_gh_remote; then
  issues="$(run_guarded 6 gh issue list --state open --limit 10 2>/dev/null)"
  [ -n "$issues" ] && out="$out
[열린 이슈]
$issues"
fi
# handoff — read-only inject (자동 git pull 제거: 세션시작 훅이 작업트리를 건드리면 안 됨.
# 동기화는 사용자가 명시적으로 git pull. 여기선 현재 HANDOFF.md만 읽어 주입.)
if in_git_repo; then
  hf="$(git rev-parse --show-toplevel 2>/dev/null)/docs/handoff/HANDOFF.md"
  if [ -f "$hf" ]; then
    handoff=""
    if command -v node >/dev/null 2>&1 && [ -f "$hook_dir/handoff-context.mjs" ]; then
      handoff="$(run_guarded 3 node "$hook_dir/handoff-context.mjs" "$hf")"
    fi
    [ -n "$handoff" ] || handoff="[인계 생략] source: docs/handoff/HANDOFF.md — bounded reader unavailable; read relevant sections on demand."
    out="$out
$handoff"
  else
    out="$out
[인계 없음] docs/handoff/HANDOFF.md 없음 — 첫 비단순 작업 종료 시 dev-protocol §5.5가 ai-working templates/HANDOFF.md로 생성한다."
  fi
  # wiki registry — one read-only line when this repo has no knowledge connection.
  # Silent when the resolver or a machine-local registry is absent (other machines, fixtures).
  resolver="$HOME/.claude/skills/project-wiki-context/scripts/wiki_context.py"
  if [ "${AI_WORKING_STARTUP_WIKI:-1}" = 1 ] && [ -f "$resolver" ] && command -v python3 >/dev/null 2>&1; then
    wiki="$(run_guarded 3 python3 "$resolver" doctor --project "$PWD" | jq -r 'select(.mode=="repo-only" and .reason=="registry entry not found") | "[wiki 미연결] remote \((.normalized_remotes[0] // "없음")) 는 knowledge registry에 없어 wiki 지식 없이 repo-only로 진행한다. 연결: 개인 repo는 wiki .system/scripts/connect_project_wiki.py --personal --slug <slug> (dry-run 후 승인 시 --apply); 업무 repo는 registry에 common-only 항목을 먼저 추가하면 knowns 첫 저장 시 connect를 제안한다."' 2>/dev/null)"
    [ -n "$wiki" ] && out="$out
$wiki"
  fi
fi
# Rule 9 — disk guard (하루 1회만 du; 매 세션 전체 재귀스캔 비용 제거)
dstamp="$HOME/.claude/.disk-stamp"
if [ "${AI_WORKING_STARTUP_DISK:-0}" = 1 ] && { [ ! -f "$dstamp" ] || [ -n "$(find "$dstamp" -mtime +1 2>/dev/null)" ]; }; then
  : > "$dstamp"
  big="$(run_guarded 5 du -sg "$HOME/.claude/projects" 2>/dev/null | awk '$1>=14{print}')"
  [ -n "$big" ] && out="$out
[디스크] ~/.claude/projects 14GB+ — 정리 후보 검토 권장(큰 .jsonl/안 쓰는 서버·도커). 삭제는 확인 후."
fi
[ -n "$out" ] && jq -n --arg c "$out" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$c}}'
exit 0
