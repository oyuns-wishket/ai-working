# Tooling and installation

마지막 검증일: 2026-07-29.

## Sources and pinned defaults

| 도구 | 기본 버전·source | 역할 | 라이선스 |
|---|---|---|---|
| Agent Skills CLI | `skills@1.5.20` | Taste Skill을 Claude/Codex에 설치 | package/repository 확인 |
| Taste Skill | `Leonxlnx/taste-skill` | 디자인 방향·redesign 지침 | MIT |
| Impeccable | `impeccable@3.4.0` | 디자인 context, commands, 60-rule detector | Apache-2.0 |

공식 source:

- `https://github.com/Leonxlnx/taste-skill`
- `https://github.com/pbakaus/impeccable`
- `https://impeccable.style/docs/detector/`

업데이트는 별도 작업으로 검증한다. 실행 중 조용히 `latest`로 바꾸지 않는다.

## Exact installation commands

Taste Skill:

```bash
npx --yes skills@1.5.20 add https://github.com/Leonxlnx/taste-skill \
  --skill <selected-skill> \
  --agent claude-code codex \
  --yes \
  --copy
```

Impeccable:

```bash
npx --yes impeccable@3.4.0 skills install \
  -y \
  --providers=claude,codex \
  --scope=project
```

설치 결과:

- `.claude/skills/<skill>/`
- `.agents/skills/<skill>/`
- `skills-lock.json`
- Impeccable hook 설정인 `.claude/settings.local.json`, `.codex/hooks.json`

기존 설정 파일은 설치 전후 diff를 확인한다.

## Skill choice

| 모드 | Taste Skill |
|---|---|
| `new` | `design-taste-frontend` |
| `rebrand` | `redesign-existing-projects` |
| `refactor` | `redesign-existing-projects` |
| `small-feature` | 없음 |
| `audit` | 없음 |

`gpt-taste`는 Codex 중심의 강한 layout/motion 실험을 사용자가 원할 때만 명시적으로 선택한다. Claude/Codex 공용 기본값으로 쓰지 않는다.

`design-taste-frontend`는 현재 v2 experimental이다. 새 프로젝트에서 대표 화면으로 먼저 검증한다. 기존 프로젝트는 `redesign-existing-projects`를 사용한다.

## Security and update boundary

- 설치 전에 CLI가 표시하는 source와 security assessment를 확인한다.
- 설치된 `SKILL.md`, scripts, hooks는 코드와 같은 신뢰 경계로 리뷰한다.
- 전역 scope를 사용하지 않는다.
- 기존 provider 설치가 서로 다르면 자동 overwrite하지 않는다.
- `skills-lock.json`과 설치 diff를 버전 증거로 보존한다.
- 새 버전은 별도 branch에서 changelog, generated diff, representative UI를 검증한 뒤 올린다.

## Current-session behavior

에이전트는 일반적으로 세션 시작 시 스킬을 탐색한다. 설치 직후 현재 세션에서 자동 호출되지 않으면:

1. 설치된 `SKILL.md`를 직접 읽어 이번 작업에 적용한다.
2. 다음 세션부터 자동 discovery되는지 확인한다.
3. 발견되지 않으면 두 provider 경로와 frontmatter를 검증한다.
