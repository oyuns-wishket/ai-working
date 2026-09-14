# Tooling and installation

도구 버전 정본: 2026-07-29. 설치 경계·웹 도구 선택 지침 검토: 2026-09-14. 이번 개편은 고정된 외부 도구 버전을 올리지 않는다.

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

먼저 설치가 필요한지 판단한다. 기존 지침·컴포넌트와 사용 가능한 검사로 충분한 작은 수정은 이 설치 단계를 건너뛰고 근거를 남긴다. 아래 모드별 값은 **설치하기로 선택했을 때의 기본값**이며 매 작업의 필수 설치 목록이 아니다. 보조 스킬이 없어도 native 방식으로 같은 사용자 승인·디자인 검증을 수행한다.

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
- `audit` dry-run은 설치 명령·생성 파일이 비어 있고 `audit --apply`는 거부한다. 기존 detector만 사용하며 없으면 직접 조사 결과와 검사 공백을 보고한다.
- 전역 scope를 사용하지 않는다.
- 기존 provider 설치가 서로 다르면 자동 overwrite하지 않는다.
- 스크립트는 양쪽 `SKILL.md` 존재·비어 있지 않음과 파일 내용 일치를 확인한다. 한쪽 누락·빈 entrypoint·파일이 아닌 entrypoint·양쪽 내용 차이가 있으면 설치를 멈춘다. YAML이나 지침의 의미적 정확성을 검증하는 기능은 아니므로 설치 파일 리뷰는 별도로 수행한다.
- `skills-lock.json`과 설치 diff를 버전 증거로 보존한다.
- 새 버전은 별도 branch에서 changelog, generated diff, representative UI를 검증한 뒤 올린다.

## Current-session behavior

에이전트는 일반적으로 세션 시작 시 스킬을 탐색한다. 설치 직후 현재 세션에서 자동 호출되지 않으면:

1. 설치된 `SKILL.md`를 직접 읽어 이번 작업에 적용한다.
2. 다음 세션부터 자동 discovery되는지 확인한다.
3. 발견되지 않으면 두 provider 경로와 frontmatter를 검증한다.

## Web implementation tools are a separate decision

Taste and Impeccable are agent guidance/inspection tools. This installer does not install app animation, chart, or 3D dependencies. Select those through [experience-routing.md](experience-routing.md), after checking the project's existing packages and official current documentation. Install only after the relevant implementation gate is unlocked, with the project's package manager. Do not add every candidate or switch frameworks to use a favored tool.

For standalone non-Git artifacts, do not run this Git-only installer. Use available tools and the native interview/comp workflow; see [standalone-visuals.md](standalone-visuals.md).
