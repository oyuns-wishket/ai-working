#!/bin/bash
# 클립보드 이미지 자동 감시 → 바뀌면 미니로 전송.
# 맥북에서 이미지 캡쳐/복사하는 순간 미니 클립보드에 자동 주입 → 미니에서 ⌘V.
# send-clip.sh를 재사용(전송 1구현). 텍스트 클립보드는 pngpaste 실패 → 무시.
PNGPASTE="/opt/homebrew/bin/pngpaste"
SEND="$HOME/.config/remote-clip/send-clip.sh"
last=""
while true; do
  tmp="$(mktemp /tmp/clipwatch.XXXXXX)"
  if "$PNGPASTE" "$tmp" >/dev/null 2>&1; then
    h="$(/sbin/md5 -q "$tmp" 2>/dev/null || md5 -q "$tmp" 2>/dev/null)"
    if [ -n "$h" ] && [ "$h" != "$last" ]; then
      last="$h"
      /bin/bash "$SEND" >/dev/null 2>&1
    fi
  fi
  rm -f "$tmp"
  sleep 1
done
