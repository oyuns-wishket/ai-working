#!/bin/bash
# PostToolUse Hook: 편집 직후 "단일 파일" 린트 피드백 → JSON additionalContext로 모델 도달.
# 수정점(audit R3): 전체 프로젝트 tsc(대형repo 20s초과→무성 fail-open) 제거 →
#   편집한 그 파일만 로컬 eslint(파일범위·빠름). 타임아웃 시 'skipped' 명시(무성 실패 금지).
#   전체 타입정합은 완료기준 prose(build 1회 실측)에 위임.
INPUT=$(cat /dev/stdin)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
{ [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ]; } && exit 0

TO="$(command -v gtimeout || command -v timeout || true)"
guard() { if [ -n "$TO" ]; then "$TO" 15 "$@"; else "$@"; fi; }

EXT="${FILE_PATH##*.}"
FEEDBACK=""
case "$EXT" in
  ts|tsx|js|jsx)
    PROJECT_DIR=$(dirname "$FILE_PATH")
    while [ "$PROJECT_DIR" != "/" ]; do
      if [ -f "$PROJECT_DIR/package.json" ]; then
        ESLINT="$PROJECT_DIR/node_modules/.bin/eslint"   # 로컬 설치본만 — 없으면 skip
        if [ -x "$ESLINT" ]; then
          OUT=$(cd "$PROJECT_DIR" && guard "$ESLINT" --no-error-on-unmatched-pattern "$FILE_PATH" 2>&1)
          if [ "$?" = "124" ]; then
            FEEDBACK="ESLint skipped (timeout) — 완료 시 build/lint 1회 실측 권장."
          else
            ERRORS=$(printf '%s' "$OUT" | grep -iE '[0-9]+:[0-9]+|error|warning' | head -5)
            [ -n "$ERRORS" ] && FEEDBACK="ESLint($FILE_PATH):
$ERRORS"
          fi
        fi
        break
      fi
      PROJECT_DIR=$(dirname "$PROJECT_DIR")
    done
    ;;
  py)
    if command -v ruff >/dev/null 2>&1; then
      ERRORS=$(guard ruff check "$FILE_PATH" 2>&1 | head -5)
      [ -n "$ERRORS" ] && FEEDBACK="Ruff($FILE_PATH):
$ERRORS"
    fi
    ;;
esac

[ -n "$FEEDBACK" ] && jq -n --arg c "$FEEDBACK" '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$c}}'
exit 0
