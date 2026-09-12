---
name: claude-setup
description: Bootstrap the ai-working Claude Code governance setup on a Mac, including global policy imports, hooks, workspace rules, and skills. Use for "claude-setup", "클코 세팅", "새 컴 클로드 세팅", "거버넌스 부트스트랩", "hook 세팅 깔아줘", or "다른 맥에 클코 세팅".
---

# claude-setup — Claude Code 거버넌스 부트스트랩 (다른 맥 재현)

## Overview
이 맥에 CLAUDE.md 계층, hooks, workspace 규칙, skills를 한 번에 연결한다. 홈 디렉터리는 `$HOME`, 프로젝트 위치는 manifest와 사용자 설정에서 해석한다. **멱등**이라 여러 번 실행해도 안전해야 한다.

## 무엇이 어디서 오나 (SSOT)
| 자산 | SSOT | 동기화 |
|---|---|---|
| `~/.claude/settings.json` (hooks 와이어링) | `$AI_WORKING_ROOT/global/governance-hooks.json` | `bootstrap.sh`가 기존 설정에 병합해 머신 고유 설정·토큰 보존 |
| 공통 글로벌 정책 | `global/CLAUDE.md` | bootstrap이 Claude import와 Codex `AGENTS.md`에 연결 |
| workspace 규칙 | `workspaces/`와 `manifest.json` | bootstrap이 선언된 대상에 연결 |
| **`~/.claude/hooks/*`** | 저장소 루트 **`hooks/`** | bootstrap이 복사 |
| 프로젝트 템플릿 | ai-working `templates/` | git pull, 신규 프로젝트에 opt-in |
| `~/.claude/CLAUDE.md` (OMC) | OMC 소유 | 각 맥 OMC가 재생성. **건드리지 않음** |

## 선행
- [AI] 현재 checkout이나 설치된 skill link에서 `AI_WORKING_ROOT`를 찾은 뒤 `git -C "$AI_WORKING_ROOT" pull --ff-only`로 최신화한다.
- 기존 Claude 설정과 플러그인은 보존한다. 특정 orchestration plugin 설치를 bootstrap의 전제로 삼지 않는다.

## 절차
1. **[AI] 의존성 확인**: README와 bootstrap의 현재 요구사항을 확인해 누락된 도구만 설치한다. 계정 로그인, 비밀번호, TCC 승인은 사용자에게 정확한 화면과 이유를 안내한다.
2. **[AI] 적용**: `bash "$AI_WORKING_ROOT/bootstrap.sh"`. 기존 `~/.claude/CLAUDE.md`를 덮지 않고 `AI-WORKING` 마커 안에 정책 import를 멱등 주입해야 한다.
3. **[AI] hooks 확인**: 저장소 루트 `hooks/`의 스크립트가 `~/.claude/hooks/`에 복사되고 실행 권한이 있는지 확인한다.
4. **[AI] 스킬 링크 확인**: 모든 `ai-working/skills/*`가 `~/.claude/skills/`와 `~/.agents/skills/`에서 같은 공개 정본을 가리키는지 확인한다.
5. **[AI] settings 병합 확인**: `global/governance-hooks.json`의 command가 기존 `~/.claude/settings.json`에 중복 없이 병합됐는지 확인한다.
6. **[AI] 검증**: `bootstrap.sh --status`, JSON 유효성, 링크 해석, 각 hook 스모크테스트를 실행한다.

## 검증 게이트
```sh
echo '{"cwd":"'"$HOME"'/projects/example-project","source":"startup"}' | ~/.claude/hooks/session-start.sh   # 유효 JSON
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | ~/.claude/hooks/pre-tool.sh  # 무출력=허용(정상)
```
- pre-tool은 `supabase db push`(비-dry-run)를 **deny**(ask 아님 — bypassPermissions에서 ask 무력이라 deny로 강제). 단 그 deny 테스트를 셸에 직접 echo하면 **라이브 훅이 그 테스트 명령을 자기차단**하니, 검증은 위 '무출력=허용'으로 하고 deny는 새 세션에서 실제 마이그 시도 시 확인.
- 새 Claude Code 세션에서 SessionStart 컨텍스트(이슈/git 정보)가 뜨면 성공.

## Supabase Branching 프로젝트 권장 설정
- **Supabase 브랜치 시드**: Supabase Branching을 쓰는 프로젝트는 `supabase/seed/*.sql`과 `config.toml [db.seed].sql_paths`로 preview 검증에 필요한 비밀 없는 테스트 데이터를 선언할 수 있다. 실제 고객 데이터와 운영 credential은 seed에 넣지 않는다.

## 트러블슈팅
| 증상 | 원인 | 대응 |
|---|---|---|
| hook 미발화 | settings 심링크/스키마 | `/sync-consortium` + `jq .hooks ~/.claude/settings.json` 확인 |
| "command not found: gtimeout" | coreutils 미설치 | `brew install coreutils`(없어도 settings의 per-hook timeout이 가드) |
| 한글입력/원격 등 | 별개 도메인 | `remote-setup` 스킬 |

> 과거 설계 기록을 보존해야 하면 비밀과 고객 정보를 제거한 뒤 이 저장소의 `docs/`에 둔다.
