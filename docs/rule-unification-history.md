# Claude·Codex 규칙 통일 개선 이력

Claude Code와 Codex가 **같은 규칙을 같은 순서로** 읽게 만든 개선의 기록이다. 다음 개선 때나 다른 모델로
재검증할 때 이 문서의 「검증 방법」을 그대로 실행해 결과를 비교한다. 고객 repo 이름·경로·계정은 이 공개 문서에
적지 않고 역할로만 부른다.

## 목표 상태 (불변식)

1. 규칙은 세 층뿐이다. 뒤 층이 앞 층을 구체화하고, 충돌하면 더 구체적인 층이 이긴다.

   | 층 | 정본 | Claude 진입 | Codex 진입 |
   |---|---|---|---|
   | 전역 | `global/CLAUDE.md` | `~/.claude/CLAUDE.md`가 `@` import | `~/.codex/AGENTS.md` symlink |
   | workspace | `workspaces/project-root/CLAUDE.md` | `<workspace>/CLAUDE.md` symlink | `<workspace>/AGENTS.md` symlink + root marker |
   | 프로젝트 | 각 repo의 루트 본문 하나 | `CLAUDE.md` | `AGENTS.md` |

2. 프로젝트 본문은 **파일 하나**다. `AGENTS.md`가 본문이면 `CLAUDE.md`는 정확히 `@AGENTS.md` 한 줄이다. 반대로
   `CLAUDE.md`가 본문이면 `AGENTS.md`는 `CLAUDE.md`로 가는 symlink다. 본문 안에서 `@path` import를 쓰지 않는다.
   Codex는 `@`를 따라가지 않고 글자 그대로 읽는다.
3. 항상 적용되는 프로젝트 규칙은 본문 안에 있다. `.claude/rules/`에는 경로 한정(`paths:`) 규칙과 Codex 용량에
   들어가지 않는 큰 규칙만 남긴다. 남긴 파일은 본문 「규칙 파일」 절에 언제 읽을지와 함께 적는다. Claude는
   `.claude/rules/`를 자동으로 읽지만 Codex는 읽지 않는다.
4. 에이전트 행동 규칙(응답 언어, plan 진입, 승인 재사용, 검증·인계)은 전역 층에만 둔다. 프로젝트 본문에는
   프로젝트 고유 사실(스택, 명령어, 도메인·보안·인프라 불변식)만 둔다. 팀 템플릿에서 복사된 행동 규칙은 두지 않는다.
5. Codex가 지시문으로 자동 로드하는 하위 `AGENTS.md`에 자동 생성 코드 지도 같은 비규칙 문서를 두지 않는다.

## 왜 바꿨나 (발견된 결함)

- 규칙 파일 이름이 repo마다 달랐다. `CLAUDE.md`만 있는 repo, `AGENTS.md`만 있는 repo, 둘이 서로 다른 내용으로
  따로 관리되는 repo가 섞여 있었다.
- Claude만 `.claude/rules/`를 자동으로 읽었다. 같은 작업에서 Codex는 env 안전, 디자인 시스템, 권한 같은 항상
  적용 규칙을 보지 못했다.
- Codex 기본 project-doc 용량(32KiB)이 전역+workspace+프로젝트 합계보다 작았다. 뒤쪽 규칙이 잘릴 위험이 있었다.
- Codex root는 기본적으로 repo root(`.git`)라서 workspace 공통 규칙(`~/<workspace>/AGENTS.md`)을 읽지 못했다.
- 팀 템플릿에서 온 행동 규칙(매 단계 commit·push 재확인, plan 모드 강제, 1Password env, 응답 규칙)이 전역 정책과
  충돌하거나 중복됐다.
- 템플릿이 자동 생성한 하위 `AGENTS.md` 20여 개가 Codex에 지시문으로 주입되고 있었다.

## 단계별 변경 (2026-10-11 ~ 10-12)

| 단계 | 변경 | 위치 |
|---|---|---|
| 1 | 전역: Claude는 import, Codex는 symlink로 같은 `global/CLAUDE.md`를 읽게 연결 | bootstrap manifest |
| 2 | workspace: `CLAUDE.md`·`AGENTS.md`를 같은 정본으로 symlink. Codex `project_root_markers = [".codex-workspace-root"]`, workspace 루트에 marker 파일 생성 | 각 Mac `~/.codex/config.toml` |
| 3 | 프로젝트 37개: 루트 진입점을 한 파일로 통일(symlink 또는 `@AGENTS.md`) | 각 프로젝트 repo 기본 브랜치 |
| 4 | Codex `project_doc_max_bytes = 65536` | 각 Mac `~/.codex/config.toml` |
| 5 | 9개 repo: 항상 적용 `.claude/rules`를 본문으로 이동, 남은 규칙은 「규칙 파일」 절에 목록화, 죽은 참조 수정 | 각 프로젝트 repo |
| 6 | 진입점 두 개가 다른 내용이던 repo: 합집합으로 합치고(다르면 더 엄격한 쪽) `CLAUDE.md` = `@AGENTS.md` | 해당 repo와 그 앱 하위 폴더 |
| 7 | workspace 규칙·프로젝트 템플릿을 위 불변식으로 갱신 | `workspaces/project-root/CLAUDE.md`, `templates/project-CLAUDE.md` |
| 8 | 템플릿 파생 repo 3개: 템플릿 행동 규칙, 템플릿 skill, `.cursor/rules`, 자동 생성 하위 `AGENTS.md`, `plansDirectory` 제거. 템플릿에 없던 프로젝트 고유 규칙만 남김 | 해당 repo |

알려진 부작용: workspace marker 때문에 workspace 밖 repo의 하위 폴더에서 Codex를 띄우면 repo 루트 `AGENTS.md`를
찾지 못한다. repo 루트에서 띄우거나, 그 repo에 marker를 둔다.

## 판단 기준 (다음 개선 때 재사용)

- **본문으로 옮길지**: frontmatter에 `paths:`가 없으면 항상 적용 규칙이다. `globs:`·`description:`만 있어도
  Claude는 항상 로드하므로 항상 적용으로 본다. 작은 것부터 옮기고, 본문이 약 32,000 bytes를 넘으면 멈춘다.
- **참조 수정 범위**: 스크립트 메시지, CI, skill, agent, 현재 명세·README, 소스 주석은 고친다. lessons,
  impl-notes, 보고서, 과거 계획, migration SQL 같은 과거 기록은 그대로 둔다.
- **템플릿 파생 판별**: 원본 템플릿과 diff해서 프로젝트가 추가한 줄만 남긴다. 템플릿 원문과 같거나 브랜치 이름만
  바꾼 파일은 템플릿 규칙으로 보고 지운다.
- **안전장치 유지**: 규칙이 옮겨 가면 그 경로를 보호하던 사람 승인 목록 같은 게이트도 새 경로로 옮긴다.
- **본문 파일을 읽는 스크립트**: `CLAUDE.md` 내용을 검사하는 스크립트가 있으면 `@AGENTS.md` import를 인정하도록 같이 고친다.

## 검증 방법 (다른 모델로 재실행)

workspace 아래 각 repo에서 아래를 실행해 기대값과 비교한다.

```bash
# 1. 진입점이 한 파일인가: 둘 중 하나여야 한다
readlink AGENTS.md                      # → CLAUDE.md
cat CLAUDE.md                           # → @AGENTS.md (한 줄)

# 2. 본문에 @import가 없는가
grep -nE '^\s*@[A-Za-z~./]' "$(readlink AGENTS.md >/dev/null && echo CLAUDE.md || echo AGENTS.md)"   # → 출력 없음

# 3. 항상 적용 규칙이 파일로 남아 있지 않은가 (남았다면 용량 사유로 본문 「규칙 파일」에 있어야 한다)
find .claude/rules -name '*.md' 2>/dev/null | while read -r f; do head -5 "$f" | grep -q '^paths:' || echo "always-on file: $f"; done

# 4. 남은 rule 파일이 본문에 모두 나열됐는가
find .claude/rules -name '*.md' 2>/dev/null | while read -r f; do grep -qF "$f" AGENTS.md CLAUDE.md || echo "unlisted: $f"; done

# 5. 자동 생성 하위 AGENTS.md가 없는가
git ls-files '*AGENTS.md' | grep -v '^AGENTS.md$' | grep -v '^\.claude/skills/' | xargs -r grep -l -E 'Generated:|Parent:'

# 6. Codex가 실제로 세 층을 다 읽는가 (각 층 고유 문구로 확인)
codex debug prompt-input | grep -c '<전역 문서 제목>'        # → 1
codex debug prompt-input | grep -c '<workspace 문서 제목>'   # → 1
codex debug prompt-input | grep -c '<프로젝트 본문 고유 문구>' # → 1 이상

# 7. 용량
wc -c AGENTS.md CLAUDE.md               # 본문 ≤ 32000, 전역+workspace+본문 합계 < project_doc_max_bytes
```

2026-10-12 결과: 세 층 로드(6번)를 확인한 repo 4개에서 모두 1/1/1이었다. 단계 5·6의 PR 9개와 단계 8의 PR 3개는
모두 CI 통과 후 병합했다. 단계 8의 repo 하나는 CI가 설정되어 있지 않아 diff 검토만 했다.

## 남은 과제

- 템플릿 파생 repo의 `package.json`·`scripts/env/*`·환경 문서에 1Password 기반 env 흐름이 남아 있다. 고객 소유
  secret store로 바꿀지는 프로젝트별로 정한다.
- 일부 repo는 규칙 파일이 커서 본문에 다 들어가지 않는다(디자인 시스템 등). 요약본을 본문에 두고 원문을 경로
  한정으로 바꾸는 방안을 검토한다.
- 검증 6번은 Codex CLI의 `debug prompt-input`에 의존한다. 이 명령이 바뀌면 이 문서의 검증 절차도 고친다.
