#!/bin/sh
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/lib.sh"
payload="$(cat)"
tool="$(printf '%s' "$payload" | jq -r '.tool_name // empty' 2>/dev/null)"
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null)"
deny() { jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'; exit 0; }
# 오탐 감소: 따옴표 안 문자열 제거(=명령을 '언급'만 한 echo/문서 제외). CONFIRMED=1 앵커 판단엔 원문 cmd 사용.
scan="$(printf '%s' "$cmd" | sed -e "s/'[^']*'/''/g" -e 's/"[^"]*"/""/g')"

# bypassPermissions에선 ask 무력 → 비가역 DB 마이그레이션은 deny로 강제(escape hatch 포함).
# rm-rf/DROP/force-push 등 파괴적 명령은 block-dangerous.sh가 별도 deny.
case "$tool" in
  Bash)
    # Rule 1: DB 마이그레이션(비가역) 명령군. (탐지는 따옴표 제거한 scan, escape 판단은 원문 cmd)
    if printf '%s' "$scan" | grep -qE '(supabase[[:space:]]+db[[:space:]]+push|supabase[[:space:]]+migration[[:space:]]+up|prisma[[:space:]]+migrate[[:space:]]+deploy|prisma[[:space:]]+db[[:space:]]+push|drizzle-kit[[:space:]]+push)'; then
      # 허용: --dry-run, 또는 명령 '맨 앞'에 앵커된 CONFIRMED=1 (부분문자열 우회 차단)
      if printf '%s' "$cmd" | grep -qE -- '--dry-run'; then :
      elif printf '%s' "$cmd" | grep -qE '^[[:space:]]*CONFIRMED=1[[:space:]]'; then :
      else
        deny "Rule 1: '<명령> --dry-run'(지원 시)으로 대상·diff를 확인하고 기존 승인 범위와 대조한 뒤 'CONFIRMED=1 <명령>'으로 실행. 같은 범위의 기존 승인은 재사용한다(dev-protocol). 새 파괴적 변경·미승인 운영 범위만 추가 확인한다."
      fi
    fi
    ;;
esac
exit 0
