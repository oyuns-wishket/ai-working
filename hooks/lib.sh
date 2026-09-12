#!/bin/sh
# Common helpers for ~/.claude hooks. Always fail-open (never block a session).
TO="$(command -v gtimeout || command -v timeout || true)"
run_guarded() {  # run_guarded <secs> <cmd...>  — fail-open on timeout/missing timeout
  secs="$1"; shift
  if [ -n "$TO" ]; then "$TO" "$secs" "$@" 2>/dev/null; else "$@" 2>/dev/null; fi
}
in_git_repo() { git rev-parse --is-inside-work-tree >/dev/null 2>&1; }
has_gh_remote() { git remote get-url origin >/dev/null 2>&1 && command -v gh >/dev/null 2>&1; }
