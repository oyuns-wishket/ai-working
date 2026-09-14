#!/bin/sh
. "$HOME/.claude/hooks/lib.sh"
payload="$(cat)"
file="$(printf '%s' "$payload" | jq -r '.tool_input.file_path // empty' 2>/dev/null)"
[ -z "$file" ] && exit 0
out=""
# The same resolver is used by the local doctor and this advisory hook.
resolver="$(dirname "$0")/workspace-config.mjs"
workspace_root=""
if [ -f "$resolver" ]; then
  workspace_root="$(node "$resolver" match "$file" 2>/dev/null)"
  resolver_status=$?
  if [ "$resolver_status" -gt 1 ]; then
    out="[ai-working] Workspace configuration could not be read; run scripts/check_environment.mjs."
  fi
else
  out="[ai-working] Workspace resolver missing; rerun ai-working/bootstrap.sh."
fi
# 쿨다운 스탬프를 repo별로 스코프(전역 단일 stamp는 한 repo 편집이 타 repo 리마인더를 침묵시킴).
rhash="$(cd "$(dirname "$file")" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null | shasum 2>/dev/null | cut -c1-12)"
rhash="${rhash:-global}"
# Rule 7 — ERP domain reminder (24h cooldown, repo-scoped)
case "$file" in
  */src/*/erp/*|*/erp/*)
    stamp="$HOME/.claude/.erp-domain-stamp-$rhash"
    if [ ! -f "$stamp" ] || [ -n "$(find "$stamp" -mtime +1 2>/dev/null)" ]; then
      out="$out
[Rule 7] ERP 도메인 변경 감지 — 프로젝트 전용 지식은 docs/erp-domain/, 여러 ERP에 공통이면 프로젝트가 명시한 workspace 공유 도메인 문서 갱신 검토."
      : > "$stamp"
    fi ;;
esac
# Rule 12 — 인프라성 파일 편집 시 docs/infra.md 갱신 리마인더 (24h 쿨다운)
case "$file" in
  */vercel.json|*/supabase/config.toml|*/.env*|*/docker-compose*|*/Dockerfile|*/next.config.*)
    istamp="$HOME/.claude/.infra-stamp-$rhash"
    if [ ! -f "$istamp" ] || [ -n "$(find "$istamp" -mtime +1 2>/dev/null)" ]; then
      out="$out
[Rule 12] 인프라성 파일 변경 감지 — docs/infra.md(배포·환경·브랜치 워크플로우) 갱신 검토."
      : > "$istamp"
    fi ;;
esac
# 브랜치 가드 — 구성된 workspace 앱 프로젝트에서 main/develop 직접 편집 시 경고(deny 아님).
# 설정된 프로젝트 workspace 하위만 대상으로 한다. develop→feat→develop→main.
if [ -n "$workspace_root" ]; then
    gbr="$(cd "$(dirname "$file")" 2>/dev/null && git branch --show-current 2>/dev/null)"
    case "$gbr" in
      main|master|develop)
        out="$out
[브랜치] '$gbr'에서 직접 편집 중 — 프로젝트가 정한 기준 branch와 작업 전용 branch/worktree 규칙을 확인할 것." ;;
    esac
fi
# dev-protocol 게이트 감지 — 설정된 workspace의 앱 소스 편집인데 최근 2일 내 갱신된 구현노트가
# 없으면 세션×repo당 1회 안내. 키워드가 아닌 행위(소스 write) 기반이라 오발사가 적고, advisory·fail-open.
# 다일차 작업은 노트 mtime(-2일)으로 허용. 스탬프는 repo해시×세션ID 스코프, 7일 지난 것은 청소.
if [ -n "$workspace_root" ]; then
    case "$file" in
      *.ts|*.tsx|*.js|*.jsx|*.py|*.vue|*.svelte)
        sid="$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null | cut -c1-12)"
        gstamp="$HOME/.claude/.devgate-stamp-$rhash-${sid:-nosid}"
        if [ ! -f "$gstamp" ]; then
          groot="$(cd "$(dirname "$file")" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null)"
          if [ -n "$groot" ] && [ -z "$(find "$groot/docs/impl-notes" -maxdepth 1 -name '*.md' -mtime -2 -print -quit 2>/dev/null)" ]; then
            out="$out
[dev-protocol] 게이트 미통과 의심 — 최근 갱신된 구현노트(docs/impl-notes/) 없이 앱 소스 편집 중. 인터뷰·계획·Gate evidence를 통과했는지 확인하고, 스킵이면 근거 한 줄을 남길 것."
            : > "$gstamp"
            find "$HOME/.claude" -maxdepth 1 -name '.devgate-stamp-*' -mtime +7 -delete 2>/dev/null
          fi
        fi ;;
    esac
fi
# Rule 2 — TODO(issue): scan in the edited file
if grep -qE 'TODO\(issue\):|FIXME\(issue\):' "$file" 2>/dev/null; then
  out="$out
[Rule 2] '$file'에 TODO(issue) 발견 — 기존 요청의 승인 범위를 확인하고 내용을 확정해 GitHub 이슈 등록 여부를 판단할 것."
fi
[ -n "$out" ] && jq -n --arg c "$out" '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$c}}'
exit 0
