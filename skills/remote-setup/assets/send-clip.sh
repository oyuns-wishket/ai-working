#!/bin/bash
# remote-setup helper: send the viewer's image clipboard to a configured host.
#
# 배경: JumpDesktop Fluid의 클립보드 동기화는 "텍스트"까지만 자동이고, 이미지 클립보드는
#       전송 대상이 아니다(사양). 그래서 이미지는 이 스크립트로 따로 쏜다.
#
# 설치 위치: ~/.config/remote-clip/send-clip.sh  (chmod +x)
# 트리거: clip-watch.sh(launchd 자동 감시)가 이미지 클립보드 변화 시 호출.
#         (수동 단축키 방식은 폐기 — JumpDesktop 포커스 시 키가 미니로 넘어가 불안정했음)
# Requires public-key SSH to the alias in REMOTE_SSH_TARGET.

REMOTE_SSH_TARGET="${REMOTE_SSH_TARGET:-}"
REMOTE_HOME="${REMOTE_HOME:-}"
REMOTE_CLIP_DIR="${REMOTE_CLIP_DIR:-${REMOTE_HOME:+$REMOTE_HOME/Desktop/_clip}}"
[[ -n "$REMOTE_SSH_TARGET" && -n "$REMOTE_HOME" && -n "$REMOTE_CLIP_DIR" ]] || {
  echo "REMOTE_SSH_TARGET, REMOTE_HOME, and REMOTE_CLIP_DIR are required." >&2
  exit 2
}
[[ "$REMOTE_SSH_TARGET" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "REMOTE_SSH_TARGET must be an SSH config alias." >&2; exit 2; }
[[ "$REMOTE_HOME" == /* && "$REMOTE_CLIP_DIR" == /* && "$REMOTE_HOME" != *".."* && "$REMOTE_CLIP_DIR" != *".."* ]] || {
  echo "Remote paths must be absolute and cannot contain '..'." >&2
  exit 2
}
[[ "$REMOTE_HOME" =~ ^/[A-Za-z0-9._/-]+$ && "$REMOTE_CLIP_DIR" =~ ^/[A-Za-z0-9._/-]+$ ]] || {
  echo "Remote paths may contain letters, digits, dot, underscore, slash, and hyphen only." >&2
  exit 2
}
PNGPASTE="${PNGPASTE:-$(command -v pngpaste 2>/dev/null || true)}"
[[ -x "$PNGPASTE" ]] || { echo "pngpaste is required." >&2; exit 1; }

notify() { /usr/bin/osascript -e "display notification \"$2\" with title \"$1\"" >/dev/null 2>&1; }

ts="$(date +%Y%m%d-%H%M%S)"
fname="clip-${ts}.png"
tmp="/tmp/${fname}"

# 1) 맥북 클립보드 이미지 추출 (이미지 없으면 종료)
if ! "$PNGPASTE" "$tmp" >/dev/null 2>&1; then
  notify "클립보드 전송" "클립보드에 이미지가 없어요"
  exit 1
fi

# 2) Upload through the configured SSH alias.
remote_abs="${REMOTE_CLIP_DIR%/}/${fname}"
printf -v remote_dir_q '%q' "$REMOTE_CLIP_DIR"
printf -v remote_abs_q '%q' "$remote_abs"
if ! ssh -o BatchMode=yes "$REMOTE_SSH_TARGET" "mkdir -p -- $remote_dir_q && cat > $remote_abs_q" < "$tmp"; then
  notify "클립보드 전송" "전송 실패 (미니/네트워크 확인)"
  rm -f "$tmp"
  exit 1
fi

# 3) Inject the uploaded image into the remote clipboard.
if ssh -o BatchMode=yes "$REMOTE_SSH_TARGET" /usr/bin/osascript - "$remote_abs" 2>/dev/null <<'APPLESCRIPT'
on run argv
  set imageFile to POSIX file (item 1 of argv)
  set the clipboard to (read imageFile as «class PNGf»)
end run
APPLESCRIPT
then
  notify "클립보드 전송" "미니로 보냄 → ⌘V로 붙여넣기"
else
  notify "클립보드 전송" "파일은 전송됨(_clip), 클립보드 주입 실패"
fi

rm -f "$tmp"
