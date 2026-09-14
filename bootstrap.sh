#!/usr/bin/env bash
# ai-working — public Claude × Codex SSOT installer
# ./bootstrap.sh [--pull] [--dry-run|--status] [--target-root PATH]
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$REPO_DIR/manifest.json"
TARGET_ROOT="${AI_WORKING_TARGET_ROOT:-$HOME}"
TS="$(date +%Y%m%d-%H%M%S)"
PULL=0
DRY=0
STATUS=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --pull) PULL=1; shift ;;
    --dry-run) DRY=1; shift ;;
    --status) STATUS=1; shift ;;
    --target-root) [ "$#" -ge 2 ] || { echo "--target-root 값이 필요합니다." >&2; exit 2; }; TARGET_ROOT="$2"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^#//'; exit 0 ;;
    --private-dir|--migrate-claude-skills-link) echo "$1은 public-only 구조에서 제거되었습니다. ai-working 하나만 사용하세요." >&2; exit 2 ;;
    *) echo "알 수 없는 옵션: $1" >&2; exit 2 ;;
  esac
done

case "$TARGET_ROOT" in /*) ;; *) echo "--target-root는 절대경로여야 합니다: $TARGET_ROOT" >&2; exit 2 ;; esac
command -v node >/dev/null || { echo "node가 필요합니다 (manifest 파싱)." >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3가 필요합니다 (runtime profile)." >&2; exit 1; }
[ -f "$MANIFEST" ] || { echo "manifest.json 없음: $MANIFEST" >&2; exit 1; }
# Refuse malformed configuration before changing any links or installed files.
node - "$TARGET_ROOT/.claude/settings.json" "$TARGET_ROOT/.codex/hooks.json" <<'NODE'
const fs = require('fs');
for (const file of process.argv.slice(2)) {
  if (!fs.existsSync(file)) continue;
  try {
    const value = JSON.parse(fs.readFileSync(file, 'utf8'));
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw Error();
  } catch { console.error('Invalid existing JSON; preserving configuration:', file); process.exit(1); }
}
NODE

c_ok="\033[32m"; c_skip="\033[90m"; c_act="\033[36m"; c_warn="\033[33m"; c_err="\033[31m"; c_off="\033[0m"
say(){ printf "%b%s%b\n" "$1" "$2" "$c_off"; }
if [ "$PULL" = 1 ]; then say "$c_act" "▶ git pull ..."; git -C "$REPO_DIR" pull --ff-only; fi

BACKUP_DIR="$TARGET_ROOT/.claude/backups/ai-working-$TS"
USER_SLUG="$(printf '%s' "$TARGET_ROOT" | sed 's|/|-|g')"
problems=0; changed=0; ok=0

target_path(){
  local value="${1//__USER_SLUG__/$USER_SLUG}"
  case "$value" in "~") printf '%s' "$TARGET_ROOT" ;; "~/"*) printf '%s/%s' "$TARGET_ROOT" "${value#\~/}" ;; /*) printf '%s' "$value" ;; *) printf '%s/%s' "$TARGET_ROOT" "$value" ;; esac
}
backup_path(){
  local dst="$1" rel
  case "$dst" in "$TARGET_ROOT"/*) rel="${dst#"$TARGET_ROOT"/}" ;; *) rel="external${dst}" ;; esac
  printf '%s/%s' "$BACKUP_DIR" "$rel"
}
backup_move(){
  local dst="$1" backup
  backup="$(backup_path "$dst")"; mkdir -p "$(dirname "$backup")"; mv "$dst" "$backup"
  say "$c_skip" "    (기존 항목 백업 → $backup)" >&2; printf '%s' "$backup"
}
record_change(){ say "$c_act" "$1"; changed=$((changed+1)); }

do_link(){
  local src="$1" target="$2" dst; dst="$(target_path "$target")"
  if [ ! -e "$src" ]; then say "$c_err" "  ✗ 원본 없음: $src"; problems=$((problems+1)); return; fi
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then say "$c_skip" "  = 링크됨: $target"; ok=$((ok+1)); return; fi
  if [ "$STATUS" = 1 ]; then say "$c_warn" "  ! 링크 불일치: $target"; problems=$((problems+1)); return; fi
  record_change "  → 링크: $target"; [ "$DRY" = 1 ] && return
  mkdir -p "$(dirname "$dst")"; if [ -e "$dst" ] || [ -L "$dst" ]; then backup_move "$dst" >/dev/null; fi; ln -s "$src" "$dst"
}

remove_marker_block(){
  local file="$1" marker="$2" begin end; begin="<!-- BEGIN $marker (auto) -->"; end="<!-- END $marker (auto) -->"
  grep -qF "$begin" "$file" 2>/dev/null || return 0
  if [ "$STATUS" = 1 ]; then say "$c_warn" "  ! legacy import 남음: $marker"; problems=$((problems+1)); return; fi
  record_change "  → legacy import 제거: $marker"; [ "$DRY" = 1 ] && return
  local backup; backup="$(backup_path "$file").pre-import-cleanup"; mkdir -p "$(dirname "$backup")"; cp "$file" "$backup"
  awk -v b="$begin" -v e="$end" '$0==b{skip=1; next} skip&&$0==e{skip=0; next} !skip{print}' "$file" > "$file.tmp"; mv "$file.tmp" "$file"
}
cleanup_legacy_imports(){
  local file="$1" marker; [ -f "$file" ] || return 0
  for marker in AGENT-DEV-CONSORTIUM AGENT-RULES WISHKET-WORKING; do remove_marker_block "$file" "$marker"; done
  if grep -Eq '@.*(wishket-working|claude-skills-kit|ai-working/private|ai-working-private)/global/(CLAUDE|AI-WORKING)\.md' "$file" 2>/dev/null; then
    if [ "$STATUS" = 1 ]; then say "$c_warn" "  ! legacy raw import 남음: $file"; problems=$((problems+1));
    else
      record_change "  → legacy raw import 제거: $file"
      if [ "$DRY" != 1 ]; then
        local backup; backup="$(backup_path "$file").pre-raw-import-cleanup"; mkdir -p "$(dirname "$backup")"; cp "$file" "$backup"
        sed -E '/@.*(wishket-working|claude-skills-kit|ai-working\/private|ai-working-private)\/global\/(CLAUDE|AI-WORKING)\.md/d' "$file" > "$file.tmp"; mv "$file.tmp" "$file"
      fi
    fi
  fi
}
do_import(){
  local src="$1" into="$2" marker="$3" file begin end line block cur
  file="$(target_path "$into")"; begin="<!-- BEGIN $marker (auto) -->"; end="<!-- END $marker (auto) -->"; line="@$src"; block="$(printf '%s\n%s\n%s' "$begin" "$line" "$end")"
  cleanup_legacy_imports "$file"
  if [ -f "$file" ] && grep -qF "$begin" "$file" 2>/dev/null; then
    cur="$(awk -v b="$begin" -v e="$end" '$0==b{f=1} f{print} $0==e{f=0}' "$file")"
    if [ "$cur" = "$block" ]; then say "$c_skip" "  = import 최신: $into"; ok=$((ok+1)); return; fi
    if [ "$STATUS" = 1 ]; then say "$c_warn" "  ! import 갱신 필요: $into"; problems=$((problems+1)); return; fi
    record_change "  → import 갱신: $into"; [ "$DRY" = 1 ] && return
    local backup; backup="$(backup_path "$file").pre-import"; mkdir -p "$(dirname "$backup")"; cp "$file" "$backup"
    awk -v b="$begin" -v e="$end" -v line="$line" '$0==b{print b; print line; print e; skip=1; next} skip&&$0==e{skip=0; next} !skip{print}' "$file" > "$file.tmp"; mv "$file.tmp" "$file"
  else
    if [ "$STATUS" = 1 ]; then say "$c_warn" "  ! import 없음: $into"; problems=$((problems+1)); return; fi
    record_change "  → import 주입: $into"; [ "$DRY" = 1 ] && return
    mkdir -p "$(dirname "$file")"
    if [ -s "$file" ]; then local backup; backup="$(backup_path "$file").pre-import"; mkdir -p "$(dirname "$backup")"; cp "$file" "$backup"; fi
    { [ -s "$file" ] && printf '\n'; printf '%s\n' "$block"; } >> "$file"
  fi
}

ensure_local_memory(){
  local dst backup source_dir=""; dst="$(target_path '~/.claude/projects/__USER_SLUG__/memory')"
  if [ -d "$dst" ] && [ ! -L "$dst" ]; then say "$c_skip" "  = machine-local memory 디렉토리"; ok=$((ok+1)); return; fi
  if [ "$STATUS" = 1 ]; then say "$c_warn" "  ! machine-local memory 이관 필요"; problems=$((problems+1)); return; fi
  record_change "  → machine-local memory 디렉토리로 이관"; [ "$DRY" = 1 ] && return
  mkdir -p "$(dirname "$dst")"
  if [ -L "$dst" ]; then source_dir="$(cd "$(dirname "$dst")" && cd "$(readlink "$dst")" 2>/dev/null && pwd -P || true)"; fi
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    backup="$(backup_move "$dst")"; mkdir -p "$dst"
    if [ -n "$source_dir" ] && [ -d "$source_dir" ]; then cp -aL "$source_dir"/. "$dst"/
    elif [ -d "$backup" ]; then cp -aL "$backup"/. "$dst"/
    fi
  else mkdir -p "$dst"; fi
}

records_for_manifest(){
  node -e 'const m=require(process.argv[1]);const base=process.argv[2];for(const l of m.links||[])console.log(["L",`${base}/${l.repo}`,l.target,l.type||"file"].join("\t"));for(const i of m.imports||[])console.log(["I",`${base}/${i.import_repo}`,i.into,i.marker].join("\t"));' "$MANIFEST" "$REPO_DIR"
}
say "$c_act" "▶ ai-working public SSOT 적용  (repo: $REPO_DIR / target: $TARGET_ROOT)"
[ "$DRY" = 1 ] && say "$c_warn" "  [DRY-RUN] 실제 변경 없음"; [ "$STATUS" = 1 ] && say "$c_warn" "  [STATUS] 점검만"
while IFS=$'\t' read -r kind a b c; do [ -z "${kind:-}" ] && continue; case "$kind" in L) do_link "$a" "$b" ;; I) do_import "$a" "$b" "$c" ;; esac; done <<< "$(records_for_manifest)"
ensure_local_memory

is_managed_skill_target(){ case "$1" in */ai-working/skills/*|*/ai-working/private/skills/*|*/ai-working-private/skills/*|*/wishket-working/skills/*|*/claude-skills-kit/skills/*) return 0 ;; *) return 1 ;; esac; }
is_managed_skill_root(){ case "$1" in */ai-working/skills|*/ai-working/private/skills|*/ai-working-private/skills|*/wishket-working/skills|*/claude-skills-kit/skills) return 0 ;; *) return 1 ;; esac; }
contains_skill(){ printf '%s\n' "$DESIRED_SKILLS" | grep -qxF "$1"; }
link_skill(){
  local src="${1%/}" dst="$2" label="$3" name; name="$(basename "$src")"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then say "$c_skip" "  = 스킬 링크됨: $label/$name"; ok=$((ok+1)); return; fi
  if [ "$STATUS" = 1 ]; then say "$c_warn" "  ! 스킬 링크 불일치: $label/$name"; problems=$((problems+1)); return; fi
  if [ -d "$dst" ] && [ ! -L "$dst" ] && ! diff -rq "$src" "$dst" >/dev/null 2>&1; then say "$c_warn" "  ! 같은 이름의 실디렉토리가 다릅니다: $dst"; problems=$((problems+1)); return; fi
  record_change "  → 스킬 링크: $label/$name"; [ "$DRY" = 1 ] && return
  mkdir -p "$(dirname "$dst")"; if [ -e "$dst" ] || [ -L "$dst" ]; then backup_move "$dst" >/dev/null; fi; ln -s "$src" "$dst"
}
prepare_skill_root(){
  local root="$1" label="$2" target
  if [ -L "$root" ]; then
    target="$(readlink "$root")"
    if ! is_managed_skill_root "$target"; then say "$c_err" "  ✗ $label skills 전체 링크가 다른 저장소를 가리킵니다: $target"; problems=$((problems+1)); return 1; fi
    if [ "$STATUS" = 1 ]; then say "$c_warn" "  ! $label skills 전체 링크를 개별 링크로 전환해야 합니다"; problems=$((problems+1)); return 1; fi
    record_change "  → $label skills 전체 링크를 개별 링크 디렉토리로 전환"; [ "$DRY" = 1 ] && return 1
    backup_move "$root" >/dev/null; mkdir -p "$root"
  else [ "$DRY" = 1 ] || [ "$STATUS" = 1 ] || mkdir -p "$root"; fi
  return 0
}
prune_stale_skills(){
  local root="$1" label="$2" dst target name
  [ -d "$root" ] || return 0
  for dst in "$root"/*; do
    [ -L "$dst" ] || continue; target="$(readlink "$dst")"; is_managed_skill_target "$target" || continue; name="$(basename "$dst")"; contains_skill "$name" && continue
    if [ "$STATUS" = 1 ]; then say "$c_warn" "  ! 예전 ai-working 스킬 링크 남음: $label/$name"; problems=$((problems+1)); continue; fi
    record_change "  → 예전 ai-working 스킬 링크 제거: $label/$name"; [ "$DRY" = 1 ] || rm "$dst"
  done
}

DESIRED_SKILLS="$(for d in "$REPO_DIR"/skills/*/; do [ -d "$d" ] && basename "$d"; done | sort)"
CLAUDE_SKILLS="$(target_path '~/.claude/skills')"; CODEX_SKILLS="$(target_path '~/.agents/skills')"
say "$c_act" "▶ 스킬 링크"
claude_ready=1; prepare_skill_root "$CLAUDE_SKILLS" Claude || claude_ready=0
codex_ready=1; prepare_skill_root "$CODEX_SKILLS" Codex || codex_ready=0
for d in "$REPO_DIR"/skills/*/; do [ -d "$d" ] || continue; [ "$claude_ready" = 1 ] && link_skill "$d" "$CLAUDE_SKILLS/$(basename "$d")" claude; [ "$codex_ready" = 1 ] && link_skill "$d" "$CODEX_SKILLS/$(basename "$d")" codex; done
[ "$claude_ready" = 1 ] && prune_stale_skills "$CLAUDE_SKILLS" claude
[ "$codex_ready" = 1 ] && prune_stale_skills "$CODEX_SKILLS" codex

HOOK_TARGET="$(target_path '~/.claude/hooks')"
HOOK_NAMES="$(for f in "$REPO_DIR"/hooks/*.sh "$REPO_DIR"/hooks/*.mjs; do [ -f "$f" ] && basename "$f"; done | sort -u | paste -sd, -)"
copy_hooks(){
  local source target backup
  for source in "$REPO_DIR"/hooks/*.sh "$REPO_DIR"/hooks/*.mjs; do
    [ -f "$source" ] || continue; target="$HOOK_TARGET/$(basename "$source")"
    if [ -f "$target" ] && cmp -s "$source" "$target"; then ok=$((ok+1)); continue; fi
    if [ "$STATUS" = 1 ]; then say "$c_warn" "  ! hook 갱신 필요: $(basename "$source")"; problems=$((problems+1)); continue; fi
    record_change "  → hook: $(basename "$source")"; [ "$DRY" = 1 ] && continue
    mkdir -p "$HOOK_TARGET"; if [ -e "$target" ]; then backup="$(backup_path "$target").pre-hook"; mkdir -p "$(dirname "$backup")"; cp "$target" "$backup"; fi
    cp "$source" "$target"; chmod +x "$target"
  done
}
render_hook_config(){
  local current="$1" desired="$2" platform="${3:-Claude}"
  node - "$current" "$desired" "$HOOK_NAMES" "$platform" <<'NODE'
const fs = require("fs")
const [currentPath, desiredPath, namesText, platform] = process.argv.slice(2)
const names = new Set(namesText.split(",").filter(Boolean))
const legacyNames = new Set([...names, "preview-db-guard.mjs"])
const read = (file, fallback) => { try { return JSON.parse(fs.readFileSync(file, "utf8")) } catch (error) { if (error.code === 'ENOENT') return fallback; throw error } }
const current = read(currentPath, {})
const desired = read(desiredPath, { hooks: {} })
const managed = command => typeof command === "string" && [...legacyNames].some(name => command.includes(`/.claude/hooks/${name}`))
const hooks = { ...(current.hooks || {}) }
for (const event of Object.keys(hooks)) {
  hooks[event] = (hooks[event] || []).map(record => {
    if (!Array.isArray(record.hooks)) return record
    const kept = record.hooks.filter(hook => !managed(hook.command))
    return kept.length ? { ...record, hooks: kept } : null
  }).filter(Boolean)
  if (!hooks[event].length) delete hooks[event]
}
for (const [event, sourceRecords] of Object.entries(desired.hooks || {})) {
  const records = structuredClone(sourceRecords)
  if (platform === "Codex") for (const record of records) {
    if (event === "SessionEnd") record.matcher = "other"
    for (const hook of record.hooks || []) {
      if (event === "SessionStart") hook.additionalContextLimit = 10000
      if (event === "UserPromptSubmit") hook.additionalContextLimit = 1200
    }
  }
  hooks[event] = [...(hooks[event] || []), ...records]
}
current.hooks = hooks
process.stdout.write(`${JSON.stringify(current, null, 2)}\n`)
NODE
}
sync_hook_manifest(){
  local source="$1" target="$2" label="$3" rendered current_norm backup; [ -f "$source" ] || return
  rendered="$(render_hook_config "$target" "$source" "$label")"
  current_norm="$(node -e 'const fs=require("fs");try{process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(process.argv[1],"utf8")),null,2)+"\n")}catch{}' "$target")"
  if [ "$current_norm" = "$rendered" ]; then say "$c_skip" "  = $label hook manifest 최신"; ok=$((ok+1)); return; fi
  if [ "$STATUS" = 1 ]; then say "$c_warn" "  ! $label hook manifest 갱신 필요"; problems=$((problems+1)); return; fi
  record_change "  → $label hook manifest 교체 병합"; [ "$DRY" = 1 ] && return
  mkdir -p "$(dirname "$target")"; if [ -f "$target" ]; then backup="$(backup_path "$target").pre-hook-sync"; mkdir -p "$(dirname "$backup")"; cp "$target" "$backup"; fi
  printf '%s' "$rendered" > "$target"
}

say "$c_act" "▶ hook"; copy_hooks
sync_hook_manifest "$REPO_DIR/global/governance-hooks.json" "$(target_path '~/.claude/settings.json')" Claude
sync_hook_manifest "$REPO_DIR/global/governance-hooks.json" "$(target_path '~/.codex/hooks.json')" Codex

# The profile is reusable behavior; plugin choices and all local values stay local.
runtime_plan="$(python3 "$REPO_DIR/scripts/configure_agent_runtime.py" --home "$TARGET_ROOT" --repo "$REPO_DIR")"
runtime_count="$(printf '%s' "$runtime_plan" | node -e 'let s="";process.stdin.on("data",x=>s+=x).on("end",()=>console.log(JSON.parse(s).changes.length))')"
if [ "$runtime_count" = 0 ]; then
  say "$c_skip" "  = 공통 runtime profile 최신"; ok=$((ok+1))
elif [ "$STATUS" = 1 ]; then
  say "$c_warn" "  ! runtime profile 갱신 필요"; problems=$((problems+1))
else
  record_change "  → 공통 runtime profile 적용 ($runtime_count files)"
  [ "$DRY" = 1 ] || python3 "$REPO_DIR/scripts/configure_agent_runtime.py" --home "$TARGET_ROOT" --repo "$REPO_DIR" --apply
fi

if [ -L "$REPO_DIR/private" ]; then
  case "$(readlink "$REPO_DIR/private")" in
    *ai-working-private*|*wishket-working*)
      if [ "$STATUS" = 1 ]; then say "$c_warn" "  ! repo-local private overlay 링크 남음"; problems=$((problems+1));
      else record_change "  → repo-local private overlay 링크 제거"; [ "$DRY" = 1 ] || rm "$REPO_DIR/private"; fi ;;
  esac
elif [ -e "$REPO_DIR/private" ]; then say "$c_err" "  ✗ repo-local private 항목은 자동 삭제하지 않습니다: $REPO_DIR/private"; problems=$((problems+1)); fi

echo
if [ "$STATUS" = 1 ]; then
  if [ "$problems" = 0 ]; then say "$c_ok" "점검 완료: 정상 ${ok}개"; else say "$c_err" "점검 실패: 불일치 ${problems}개 / 정상 ${ok}개"; fi
elif [ "$DRY" = 1 ]; then say "$c_ok" "DRY-RUN 완료: 변경예정 ${changed}개 / 문제 ${problems}개 / 정상 ${ok}개"
else say "$c_ok" "적용 완료: 변경 ${changed}개 / 문제 ${problems}개 / 정상 ${ok}개"; [ -d "$BACKUP_DIR" ] && say "$c_skip" "백업: $BACKUP_DIR"; fi
[ "$problems" = 0 ]
