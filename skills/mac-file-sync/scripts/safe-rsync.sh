#!/usr/bin/env bash
set -euo pipefail

apply=0
if [[ "${1:-}" == "--apply" ]]; then
  apply=1
  shift
fi

[[ $# -eq 2 ]] || {
  echo "usage: $0 [--apply] <source-dir/> <user@host:/absolute/destination/>" >&2
  exit 2
}

source_dir="$1"
destination="$2"

[[ -d "$source_dir" ]] || { echo "원본 폴더가 없습니다: $source_dir" >&2; exit 2; }
[[ "$destination" == *:* ]] || { echo "목적지는 user@host:/absolute/path/ 형식이어야 합니다." >&2; exit 2; }
[[ "$destination" != *".."* ]] || { echo "목적지에 '..'를 사용할 수 없습니다." >&2; exit 2; }
[[ "${destination#*:}" == /* ]] || { echo "원격 목적지는 절대경로여야 합니다." >&2; exit 2; }

if [[ "$source_dir" != */ ]]; then
  echo "주의: 폴더 자체가 아니라 내용만 동기화하도록 source 끝에 / 를 붙입니다."
  source_dir="${source_dir}/"
fi

args=(
  -a
  -h
  --itemize-changes
  --stats
  --protect-args
  --exclude=.DS_Store
  -e "ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new"
)

if [[ $apply -eq 0 ]]; then
  args+=(--dry-run)
  echo "mode=dry-run (파일을 변경하지 않습니다)"
else
  echo "mode=apply (삭제 옵션 없음)"
fi

rsync "${args[@]}" -- "$source_dir" "$destination"
