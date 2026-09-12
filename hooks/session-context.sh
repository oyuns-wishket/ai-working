#!/bin/bash
# SessionStart Hook: 세션 시작 시 현재 디렉터리 컨텍스트 주입
# CWD에 따라 프로젝트 관련 정보를 자동 제공

CWD=$(pwd)
CONTEXT=""

resolve_ai_working_root() {
  if [ -n "${AI_WORKING_ROOT:-}" ] && [ -f "$AI_WORKING_ROOT/bootstrap.sh" ]; then
    printf '%s' "$AI_WORKING_ROOT"
    return 0
  fi

  local link raw resolved candidate
  for link in "$HOME/.codex/AGENTS.md" "$HOME/.agents/skills/dev-protocol" "$HOME/.claude/skills/dev-protocol"; do
    [ -L "$link" ] || continue
    raw="$(readlink "$link")"
    case "$raw" in
      /*) resolved="$raw" ;;
      *) resolved="$(cd "$(dirname "$link")" && cd "$(dirname "$raw")" 2>/dev/null && printf '%s/%s' "$PWD" "$(basename "$raw")" || true)" ;;
    esac
    [ -n "$resolved" ] || continue
    candidate="$(dirname "$(dirname "$resolved")")"
    if [ -f "$candidate/bootstrap.sh" ]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

AI_WORKING_ROOT="$(resolve_ai_working_root || true)"

# Git 정보
if git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
  BRANCH=$(git branch --show-current 2>/dev/null)
  DIRTY=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  LAST_COMMIT=$(git log --oneline -1 2>/dev/null)
  CONTEXT="Git: branch=$BRANCH, uncommitted=$DIRTY files, last commit: $LAST_COMMIT"

  # Optional project→wiki registry hint. No wiki body, pull, network, or write.
  WIKI_CONTEXT_SCRIPT="${AI_WORKING_ROOT:+$AI_WORKING_ROOT/skills/project-wiki-context/scripts/wiki_context.py}"
  if [ -n "$WIKI_CONTEXT_SCRIPT" ] && [ -f "$WIKI_CONTEXT_SCRIPT" ]; then
    WIKI_CONTEXT=$(python3 "$WIKI_CONTEXT_SCRIPT" hook --project "$CWD" 2>/dev/null || true)
    [ -n "$WIKI_CONTEXT" ] && CONTEXT="$CONTEXT | $WIKI_CONTEXT"
  fi
fi

# Node.js 프로젝트 감지
if [ -f "$CWD/package.json" ]; then
  PKG_NAME=$(jq -r '.name // "unknown"' "$CWD/package.json" 2>/dev/null)
  CONTEXT="$CONTEXT | Node project: $PKG_NAME"
fi

if [ -n "$CONTEXT" ]; then
  jq -n --arg ctx "$CONTEXT" '{
    hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: $ctx
    }
  }'
fi

exit 0
