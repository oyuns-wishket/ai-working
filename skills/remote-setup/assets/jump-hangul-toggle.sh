#!/bin/sh
# Jump Desktop 세션 중 "맥북 로컬 IME만" 한영 토글. 미니로는 키 안 보냄.
# 최적화: macism 현재상태 조회(느림) 제거 → state 파일로 즉시 flip(전환 지연 단축).
# desync 시(메뉴바로 수동변경 등) 한 번 더 누르면 자기교정.
MACISM=/opt/homebrew/bin/macism
STATE="$HOME/.config/karabiner/.hangul_state"
if [ -f "$STATE" ] && [ "$(cat "$STATE" 2>/dev/null)" = "ko" ]; then
  "$MACISM" com.apple.keylayout.ABC >/dev/null 2>&1 &
  printf en > "$STATE"
else
  "$MACISM" com.apple.inputmethod.Korean.2SetKorean >/dev/null 2>&1 &
  printf ko > "$STATE"
fi
