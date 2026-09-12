#!/bin/bash
# SessionStart Hook: 세션 시작 시 현재 디렉터리 컨텍스트 주입
# CWD에 따라 프로젝트 관련 정보를 자동 제공

CWD=$(pwd)
CONTEXT=""
AI_WORKING_ROOT="${AI_WORKING_ROOT:-$HOME/dev-oh/ai-working}"

# Git 정보
if git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
  BRANCH=$(git branch --show-current 2>/dev/null)
  DIRTY=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  LAST_COMMIT=$(git log --oneline -1 2>/dev/null)
  CONTEXT="Git: branch=$BRANCH, uncommitted=$DIRTY files, last commit: $LAST_COMMIT"

  # Optional project→wiki registry hint. No wiki body, pull, network, or write.
  WIKI_CONTEXT_SCRIPT="$AI_WORKING_ROOT/skills/project-wiki-context/scripts/wiki_context.py"
  if [ -f "$WIKI_CONTEXT_SCRIPT" ]; then
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
