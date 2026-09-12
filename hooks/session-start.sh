#!/bin/sh
. "$HOME/.claude/hooks/lib.sh"
payload="$(cat)"
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null)"
[ -n "$cwd" ] && cd "$cwd" 2>/dev/null
out=""
# Rule 3 — open issues (read-only)
if in_git_repo && has_gh_remote; then
  issues="$(run_guarded 6 gh issue list --state open --limit 10 2>/dev/null)"
  [ -n "$issues" ] && out="$out
[열린 이슈]
$issues"
fi
# handoff — read-only inject (자동 git pull 제거: 세션시작 훅이 작업트리를 건드리면 안 됨.
# 동기화는 사용자가 명시적으로 git pull. 여기선 현재 HANDOFF.md만 읽어 주입.)
if in_git_repo; then
  hf="$(git rev-parse --show-toplevel 2>/dev/null)/docs/handoff/HANDOFF.md"
  [ -f "$hf" ] && out="$out
[인계 HANDOFF.md]
$(cat "$hf")"
fi
# Rule 9 — disk guard (하루 1회만 du; 매 세션 전체 재귀스캔 비용 제거)
dstamp="$HOME/.claude/.disk-stamp"
if [ ! -f "$dstamp" ] || [ -n "$(find "$dstamp" -mtime +1 2>/dev/null)" ]; then
  : > "$dstamp"
  big="$(run_guarded 5 du -sg "$HOME/.claude/projects" 2>/dev/null | awk '$1>=14{print}')"
  [ -n "$big" ] && out="$out
[디스크] ~/.claude/projects 14GB+ — 정리 후보 검토 권장(큰 .jsonl/안 쓰는 서버·도커). 삭제는 확인 후."
fi
[ -n "$out" ] && jq -n --arg c "$out" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$c}}'
exit 0
