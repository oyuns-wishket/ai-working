---
name: sync-consortium
description: Use when the user wants to sync, apply, or pull the public ai-working Claude × Codex SSOT environment, including on a fresh Mac or after editing shared global rules and skills on another machine.
---

# sync-consortium

여러 Mac의 Claude와 Codex 개발환경을 public `ai-working` 하나에 맞춰 동기화한다.

전체 구조·변경 규칙은 `agent-environment` 스킬의 `references/claude-codex-sync.md`를 읽는다. 계정 전환은 같은 스킬의 `references/cswap.md`를 읽는다.

## 실행

진입점: 설치된 skill link나 현재 checkout에서 해석한 `$AI_WORKING_ROOT`

1. **상태부터 점검** (변경 없음):
   ```bash
   "$AI_WORKING_ROOT/bootstrap.sh" --status
   ```
2. 동기화가 필요하면 **pull + 적용**:
   ```bash
   "$AI_WORKING_ROOT/bootstrap.sh" --pull
   ```
3. 결과 리포트를 사용자에게 요약한다 (변경/정상 개수, 백업 위치).

## 동작 원리
- `manifest.json`의 매핑대로 Claude 메모리/워크스페이스 문서, Codex 글로벌 `~/.codex/AGENTS.md`, Codex 워크플로 어댑터를 레포로 심볼릭 링크.
- `~/.claude/CLAUDE.md`(OMC 소유)에는 마커로 감싼 `@import` 한 줄만 멱등 주입 → 레포의 `global/CLAUDE.md`를 끌어옴.
- 멱등: 이미 올바르면 건너뜀. 원본 실파일은 `~/.claude/backups/`로 백업 후 교체(삭제 안 함).

## 주의
- 로컬에서 규칙이나 skill을 고쳤으면 변경이 `ai-working` 작업 트리에 직접 기록됐는지 확인하고 현재 승인 범위에 따라 commit·push한다.
- 새 맥 최초 셋업이면 `bootstrap.sh`만 단독 실행(아직 클론 안 됐으면 README의 1회 클론 절차부터). 실행 후 `~/.claude/skills`와 `~/.codex/AGENTS.md`가 모두 이 레포를 가리키는지 확인한다.
