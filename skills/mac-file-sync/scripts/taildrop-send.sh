#!/usr/bin/env bash
set -euo pipefail

TAILSCALE_BIN="${TAILSCALE_BIN:-}"
if [[ -z "$TAILSCALE_BIN" ]]; then
  if command -v tailscale >/dev/null 2>&1; then
    TAILSCALE_BIN="$(command -v tailscale)"
  elif [[ -x /Applications/Tailscale.app/Contents/MacOS/Tailscale ]]; then
    TAILSCALE_BIN=/Applications/Tailscale.app/Contents/MacOS/Tailscale
  else
    echo "Tailscale CLI를 찾지 못했습니다." >&2
    exit 1
  fi
fi

target="${AI_WORKING_TAILDROP_NODE:-}"
if [[ "${1:-}" == "--to" ]]; then
  [[ $# -ge 3 ]] || { echo "usage: $0 [--to node] file [file ...]" >&2; exit 2; }
  target="$2"
  shift 2
fi

[[ $# -ge 1 ]] || { echo "usage: $0 [--to node] file [file ...]" >&2; exit 2; }

[[ -n "$target" ]] || {
  echo "대상 노드가 필요합니다. --to <tailscale-node> 또는 AI_WORKING_TAILDROP_NODE를 사용하세요." >&2
  "$TAILSCALE_BIN" status >&2 || true
  exit 2
}
[[ "$target" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || { echo "대상 노드 형식이 안전하지 않습니다." >&2; exit 2; }

files=()
for source_path in "$@"; do
  [[ -f "$source_path" ]] || { echo "일반 파일이 아닙니다: $source_path" >&2; exit 2; }
  [[ -r "$source_path" ]] || { echo "읽을 수 없습니다: $source_path" >&2; exit 2; }
  files+=("$source_path")
done

status_line="$($TAILSCALE_BIN status 2>/dev/null | awk -v node="$target" '$2 == node { print; exit }')"
[[ -n "$status_line" ]] || { echo "Tailscale에서 대상 노드를 찾지 못했습니다: $target" >&2; exit 3; }
if [[ "$status_line" == *offline* ]]; then
  echo "대상 노드가 오프라인입니다: $target" >&2
  exit 4
fi

echo "target=$target"
for source_path in "${files[@]}"; do
  size="$(stat -f '%z' "$source_path")"
  digest="$(shasum -a 256 "$source_path" | awk '{print $1}')"
  echo "send=$(basename "$source_path") bytes=$size sha256=$digest"
done

# macOS GUI 번들 CLI는 샌드박스라 파일 경로를 직접 읽지 못한다.
# 파일마다 stdin으로 파이프해 --name으로 원래 이름을 보존한다.
for source_path in "${files[@]}"; do
  "$TAILSCALE_BIN" file cp --verbose --name "$(basename "$source_path")" - "${target}:" < "$source_path"
done
