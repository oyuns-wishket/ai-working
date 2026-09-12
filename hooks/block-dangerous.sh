#!/bin/bash
# PreToolUse Hook: 파괴적 명령 차단 (best-effort — 완전 가드 아님. $()/heredoc/eval 우회 가능).
# 구조적 하드플로어는 managed-settings.json의 permissions.deny가 담당(설치 권장).
INPUT=$(cat /dev/stdin)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$COMMAND" ] && exit 0

# 오탐 감소: 따옴표 안 문자열을 비우고(=echo/printf로 패턴을 '언급'만 한 경우 제외), 주석 제거 후 매칭.
SCAN=$(printf '%s' "$COMMAND" | sed -e "s/'[^']*'/''/g" -e 's/"[^"]*"/""/g' -e 's/[[:space:]]#.*$//')

BLOCKED=""
# rm -rf 루트/홈
if echo "$SCAN" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)+(-[a-zA-Z]*f[a-zA-Z]*\s+)*(\/$|\/\s|~\/$|~\/\s|~\s*$|\$HOME\/$|\$HOME\s)'; then
  BLOCKED="rm -rf on root/home directory"
fi
# rm -rf *
if echo "$SCAN" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)+(-[a-zA-Z]*f[a-zA-Z]*\s+)*\*'; then
  BLOCKED="rm -rf * (전체 삭제)"
fi
# DROP TABLE/DATABASE — DB 실행 컨텍스트에서만
if echo "$SCAN" | grep -qiE '(psql|supabase|mysql|sqlite3|prisma|pg_|mongo)' \
   && echo "$SCAN" | grep -qiE 'DROP\s+(TABLE|DATABASE|SCHEMA)'; then
  BLOCKED="DROP TABLE/DATABASE in DB context"
fi
# force push to protected branch — 순서 무관 3조건 AND
if echo "$SCAN" | grep -qE 'git\s+push' \
   && echo "$SCAN" | grep -qE '(--force|--force-with-lease|(^|[[:space:]])-f([[:space:]]|$))' \
   && echo "$SCAN" | grep -qE '(^|[[:space:]])(main|master|prod|production)([[:space:]]|$)'; then
  BLOCKED="force push to protected branch"
fi
# git reset --hard (지정본 + bare)
if echo "$SCAN" | grep -qE 'git\s+reset\s+--hard\s+(origin|HEAD~)'; then
  BLOCKED="git reset --hard (destructive)"
fi
if echo "$SCAN" | grep -qE 'git\s+reset\s+--hard(\s+HEAD)?\s*($|;|&&|\|)'; then
  BLOCKED="git reset --hard (uncommitted 손실)"
fi
# chmod 777 루트
if echo "$SCAN" | grep -qE 'chmod\s+(-R\s+)?777\s+\/'; then
  BLOCKED="chmod 777 on root paths"
fi

if [ -n "$BLOCKED" ]; then
  jq -n --arg reason "$BLOCKED" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: ("⛔ 차단됨: " + $reason + ". 비가역/파괴적이라 거부됨 — 범위를 좁히거나(대상 경로 명시) dry-run·백업 등 더 안전한 대안을 쓰고, 꼭 필요하면 그 근거를 사용자와 확인한다.")
    }
  }'
  exit 0
fi
exit 0
