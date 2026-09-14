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

## 앱 라이브러리 설치·재사용

Taste/Impeccable는 에이전트 지침·검사 도구다. 위 스크립트는 Anime.js·Motion·Bklit·3D 앱 의존성을 설치하지 않는다. 앱에는 [experience-routing.md](experience-routing.md)의 기본 도구를 아래 절차로 에이전트가 직접 설치·연결한다.

1. 실제 앱 root, workspace package, packageManager·lockfile, framework/React 버전, 기존 import·wrapper·registry component를 확인한다. 이미 설치된 도구는 재사용하고 major upgrade를 자동 수행하지 않는다.
2. 선택한 공식 API/설치 경로가 현재 stack과 맞는지 확인한다. 사용할 새 버전은 lockfile로 기록한다. 여러 패키지 매니저를 혼용하지 않는다.
3. 대표 시안용 의존성은 분리된 preview 경로에 준비한다. **앱 소스와 앱 package/lockfile 변경은 해당 디자인 게이트가 풀린 뒤** 진행한다. audit는 둘 다 설치하지 않는다.
4. 아래 필요한 항목만 프로젝트 로컬에 추가하고 즉시 사용 코드·상태·cleanup을 연결한다. 설치돼 있다는 것과 구현에 사용됐다는 것을 구분한다.
5. diff·typecheck/build·실제 동작을 확인하고 다음 실행에서 같은 파일을 덮어쓰거나 다시 설치하지 않도록 기존 경로를 기록한다.

| 도구 | 새 설치 예시: pnpm 프로젝트 | 기존 설치의 확인과 연결 |
|---|---|---|
| Anime.js | `pnpm add animejs` | `animejs`와 기존 API 버전 확인; scope/timeline과 해제 처리, 요청한 연출에 연결 |
| Motion React | `pnpm add motion` | `motion` 또는 호환 `framer-motion`과 기존 import 확인; 새 설치는 공식 `motion/react` 경로. 기존 패키지를 중복 추가하지 않음 |
| Bklit 차트 | `pnpm dlx shadcn@<verified-version> add @bklit/line-chart` | 실제 chart source와 `components.json`의 registry/alias 확인. 해당 공식 component만 추가하고 생성된 로컬 경로로 import |
| React 3D | `pnpm add three @react-three/fiber @react-three/drei` | 기존 renderer·React peer version·loader·decoder 확인 후 선택한 GLB 연결 |

명령은 예시다. 에이전트가 실제 프로젝트 매니저와 확인한 버전으로 실행한다. Bklit의 shadcn source는 package.json에 Bklit 이름이 없을 수 있으므로 소스도 확인한다. shadcn이 없으면 필요한 초기 설정의 diff를 검토하고 기존 CSS·토큰을 보존한다. 기존 사용자 수정 파일을 강제 overwrite하지 않는다. 무료 Bklit components와 별도 Studio의 코드/권한을 구분한다.

비React 환경에는 해당 framework의 공식 Motion/Three.js 경로를 사용한다. Bklit이 호환되지 않으면 이유와 chart 대안을 [data-surfaces.md](data-surfaces.md)에 따라 기록한다. 앱 전체를 React로 옮기거나 기존 차트를 일괄 교체하지 않는다.

## 외부 앱·계정 기능

Blender/Spline 같은 desktop 앱, MCP, 생성 API는 npm 라이브러리와 별개다. [tool-capabilities.md](tool-capabilities.md)로 실제 사용 가능 기능을 정한 뒤 [ai-assisted-3d.md](ai-assisted-3d.md)의 연결·작업 흐름을 실행한다. 연결 가능한 도구를 탐색하고 공식 배포·프로젝트 지침으로 설치한다. 사용자에게 터미널이나 모델링 작업을 넘기지 않는다. 로그인·GUI 권한처럼 에이전트가 할 수 없는 동작만 정확한 위치와 이유를 설명하고 완료 후 에이전트가 재개한다.

공식 근거: [Anime.js](https://animejs.com/documentation/getting-started/installation/), [Motion](https://motion.dev/docs/react-installation), [Bklit line chart](https://bklit.com/docs/components/line-chart), [R3F](https://r3f.docs.pmnd.rs/getting-started/installation).

For standalone non-Git artifacts, do not run this Git-only installer. Use available tools and the native interview/comp workflow; see [standalone-visuals.md](standalone-visuals.md).
