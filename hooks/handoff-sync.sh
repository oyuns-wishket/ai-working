#!/bin/sh
# Stop hook: 턴/세션 끝에 HANDOFF.md를 자동 커밋·푸시 → 다른 맥에서 바로 이어감.
# 안전장치: ① docs/handoff/HANDOFF.md 있는 repo에서만(opt-in) ② 2분 디바운스 ③ HANDOFF.md만 커밋
#          ④ upstream 있을 때만 push ⑤ .handoff-no-push 있으면 push 생략 ⑥ 전부 fail-open.
. "$HOME/.claude/hooks/lib.sh"
payload="$(cat)"
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null)"
[ -n "$cwd" ] && cd "$cwd" 2>/dev/null
in_git_repo || exit 0
root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
hf="$root/docs/handoff/HANDOFF.md"
[ -f "$hf" ] || exit 0

rhash="$(printf '%s' "$root" | shasum 2>/dev/null | cut -c1-12)"
stamp="$HOME/.claude/.handoff-stamp-${rhash:-x}"
# 디바운스: 스탬프가 있고 2분 안 지났으면 skip
[ -f "$stamp" ] && [ -z "$(find "$stamp" -mmin +2 2>/dev/null)" ] && exit 0

# 기계 breadcrumb 자동 기록(에이전트 요약 없어도 '어디까지'는 남게). 타임스탬프는 안 넣어 idle churn 방지
# = 브랜치·HEAD·변경파일이 실제로 바뀔 때만 HANDOFF가 바뀜.
br="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
head="$(git rev-parse --short HEAD 2>/dev/null)"
chg="$(git status --porcelain 2>/dev/null | awk '{print $2}' | head -8 | tr '\n' ' ')"
# 기존 AUTO-CRUMB 블록 제거 후 새로 추가(끝). sed로 start~end 블록 삭제.
tmp="$(mktemp)"
sed '/<!-- AUTO-CRUMB/,/-->/d' "$hf" > "$tmp" 2>/dev/null
{ cat "$tmp"; printf '\n<!-- AUTO-CRUMB\nbranch: %s | head: %s\nchanged: %s\n-->\n' "$br" "$head" "$chg"; } > "$hf" 2>/dev/null
rm -f "$tmp"

# 변경 없으면 skip
git diff --quiet -- "$hf" 2>/dev/null && git diff --cached --quiet -- "$hf" 2>/dev/null && exit 0
: > "$stamp"

run_guarded 15 git add -- "$hf" 2>/dev/null
run_guarded 15 git commit -q -m "chore(handoff): sync" -- "$hf" 2>/dev/null
# push: upstream 있고, no-push 마커 없을 때만
if [ ! -f "$root/.handoff-no-push" ] && git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
  run_guarded 20 git push 2>/dev/null
fi
exit 0
