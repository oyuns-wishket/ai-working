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

## 설치 스크립트: 계획 → 검토 → 적용

[setup_design_tools.py](../scripts/setup_design_tools.py)는 보조 스킬 설치를 계획하며 기본 동작은 plan-only다. `<skill-dir>`은 현재 읽은 스킬 디렉토리, `<git-root>`는 확인한 대상 프로젝트의 실제 Git root, `<mode>`는 확정한 모드로 치환한다.

1. `python3 <skill-dir>/scripts/setup_design_tools.py --project <git-root> --mode <mode> --json`으로 계획만 출력한다.
2. `states_before`, source·실행 명령(`commands`)·생성 예상 파일(`expected_files`)과 기존 provider 설정 diff를 검토한다. 계획 출력은 설치 완료 증거가 아니다.
3. 설치가 필요한 구현 모드이고 기존 승인 범위에 포함되면 같은 명령에 `--apply`를 붙인다. 설치 여부마다 같은 범위의 승인을 다시 묻지 않는다. 설치 권한이 없으면 구체적인 계획을 제시하고 결정까지 적용을 보류한다.
4. 실행 결과·양쪽 provider의 실제 설치 파일·내용 일치·설정 diff를 확인한다. 앱 의존성은 이 스크립트가 설치하지 않으며 아래 앱 라이브러리 절을 따른다.

| 옵션 | 확인할 동작 |
|---|---|
| `--project <git-root>` | 실제 Git root만 허용; workspace 상위나 nested 경로에 설치하지 않음 |
| `--mode <mode>` | 아래 Skill choice의 다섯 모드 중 하나 |
| `--json` | 계획/실행 증거를 JSON으로 출력 |
| `--apply` | 검토한 설치 실행; 생략하면 plan-only, audit에서는 거부 |
| `--taste-skill <name>` | 필요한 경우 모드 기본값 재정의; `none`이면 Taste Skill 생략 |
| `--skills-version`, `--impeccable-version` | 기본값은 각각 `1.5.20`, `3.4.0`; 버전 변경은 별도 검증 작업 |

## Exact installation commands

먼저 보조 스킬의 설치 상태와 필요한 역할을 확인한다. 이미 같은 지침·검사를 사용할 수 있으면 중복 설치를 생략하고 경로를 기록한다. 보조 스킬 설치 생략은 조사·새 표현의 동작 시안·검증 강도를 낮추는 근거가 아니다. 아래 모드별 값은 **설치하기로 선택했을 때의 기본값**이며 매 작업의 필수 설치 목록이 아니다. 보조 스킬이 없어도 native 방식으로 같은 사용자 승인·디자인 검증을 수행한다.

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
- `audit` plan-only는 설치 명령·생성 파일이 비어 있고 `audit --apply`는 거부한다. 기존 detector만 사용하며 없으면 직접 조사 결과와 검사 공백을 보고한다.
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

Taste/Impeccable는 에이전트 지침·검사 도구다. 위 스크립트는 Anime.js·Motion·Bklit·3D 앱 의존성을 설치하지 않는다. 앱에는 [SKILL.md](../SKILL.md)의 기본 도구를 아래 절차로 에이전트가 직접 설치·연결한다.

1. 실제 앱 root, workspace package, packageManager·lockfile, framework/React 버전, 기존 import·wrapper·registry component를 확인한다. 기본 도구의 호환되는 설치는 재사용하고 major upgrade를 자동 수행하지 않는다. 기존 레거시 차트 엔진은 재사용 기본값이 아니라 아래 절차의 교체 대상이다.
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

명령은 예시다. 에이전트가 실제 프로젝트 매니저와 확인한 버전으로 실행한다. Bklit의 shadcn source는 package.json에 Bklit 이름이 없을 수 있으므로 소스도 확인한다. shadcn/Tailwind 도입이 필요하면 [data-surfaces.md](data-surfaces.md)의 호환 판정에 따라 도입 diff·영향 범위·토큰 매핑을 제시하고 그 도입 결정 하나를 받은 뒤 진행한다. 이미 같은 도입이 승인됐으면 재사용한다. 그 결정 없이 전역 CSS 체계를 추가하지 않는다. 기존 사용자 수정 파일을 강제 overwrite하지 않는다. 무료 Bklit components와 별도 Studio의 코드/권한을 구분한다.

비React 환경에는 해당 framework의 공식 Motion/Three.js 경로를 사용한다. Bklit이 호환되지 않으면 이유와 chart 대안을 [data-surfaces.md](data-surfaces.md)에 따라 기록한다. 프레임워크 이관 금지, 승인 없이 이번 범위 밖 화면을 교체하지 않는다. 대상 화면 이관과 전체 이관 제안은 아래 절차를 따르며, 전체 이관은 실제 사용자 결정 범위 안에서 수행한다.

## Bklit 설치 경로 확인

설치 전후에 아래 표를 기존 DESIGN의 Chart decisions 또는 구현노트에 기록한다. `package.json`에 Bklit 이름이 없다는 이유만으로 미설치로 판단하지 않는다.

| 확인 항목 | 설치 전 확인 | 설치 후 완료 증거 |
|---|---|---|
| 대상 앱·stack | 실제 앱 root·workspace package·React/framework 버전·package manager·lockfile | 동일 앱에만 생긴 manifest/lockfile diff; 호환성 확인 |
| shadcn registry | `components.json` 존재·registry 설정·현재 공식 component 주소와 설치 경로 | 선택한 registry component와 실행 명령·확인 버전 |
| alias·CSS·토큰 | `components.json`의 alias와 연결된 TS/JS 경로 설정·CSS 진입점·기존 사용자 수정; Tailwind/shadcn 도입이 필요하면 diff·영향 범위·토큰 매핑·실제 결정 | 실제 생성 파일 경로와 alias 해석; 결정한 범위의 CSS·토큰 보존 diff |
| 생성 source | 이미 생성된 chart 소스·공통 wrapper·호출 화면 검색 | 추가/재사용한 파일·실제 import 경로·사용 route; 중복 wrapper 여부 |
| 필요한 의존성 | 생성 소스가 참조하는 패키지·peer 조건 확인 | 실제 import와 lockfile 의존 경로; 불필요한 레거시와 구분 |
| 실행 | 기존 차트 상태·대표 데이터 기준선 | typecheck/build·브라우저 동작·같은 데이터 parity 증거 |

설정이 없으면 위 호환 판정과 도입 결정을 확인한 뒤 공식 초기화 경로를 적용하고 기존 CSS·토큰을 보존한다. 생성 파일에 사용자 수정이 있으면 강제 overwrite하지 않고 필요한 차이를 병합한다. 공식 경로를 확인하지 못하면 추정한 registry URL/API를 실행하지 않고 확인 공백을 기록한다.

## 레거시 차트 엔진 제거 절차

교체 정책·호환성 예외는 [data-surfaces.md](data-surfaces.md)의 레거시 차트 엔진 교체 절이 소유한다. 설치·제거는 다음 순서로 수행한다. `audit`는 인벤토리·판정·전체 이관 제안까지 대화로 보고하고 이관·설치·제거·기록 파일 생성은 하지 않는다.

1. **인벤토리:** ECharts·Chart.js·ApexCharts·Highcharts·구 Recharts wrapper 등 실제 레거시 의존성, import/require/dynamic import, alias, 공통 wrapper·테마·타입·CSS·사용 route를 조사한다. `package.json`뿐 아니라 lockfile·workspace package·생성 source·빌드 설정을 확인한다.
2. **대상 화면 이관:** 확인된 개별 차트 예외가 없는 화면은 모든 레거시 차트를 함께 이관한다. 개별 차트의 비호환 예외(필수 기능 부재·실측 성능)가 기록된 화면은 해당 차트에 한해 공존을 허용하고, 예외 범위·의존 비용·재검토 조건을 기록한다. 해당 route는 `기록된 예외`로 집계하며 `이관 완료`나 레거시 import 0건으로 표시하지 않는다. 이관할 차트의 새 표현 여부를 각각 판정한다. 디자인 게이트가 풀리면 Bklit 설치/생성 source를 실제 대상에 연결하고 기존 데이터·필터·tooltip·범례·export·권한/상태 계약을 보존한다. [verification.md](verification.md)의 같은 데이터 parity 검증을 통과시킨다. parity가 미실행이면 `이관(parity 미실행)`으로 남기고 N에 더하지 않는다. 개별 차트 예외가 있는 route는 `기록된 예외`를 유지하며 이관한 차트의 parity도 따로 기록한다. 검증 전에 사용 중인 패키지를 먼저 제거하지 않는다.
3. **전체 이관 제안:** 대상 밖 사용처가 있으면 남은 화면·공통 wrapper·필수 기능 차이·이관 순서·중복 비용·제거 조건을 구체화하고 실제 사용자 결정을 기록한다. 이미 전체 이관이 승인됐으면 재질문 없이 승인 범위에서 실행한다. 유예/예외이면 남은 route·근거·재검토 조건을 남긴다.
4. **사용처 정리:** 승인된 이관을 끝내고 parity가 통과하면 더 이상 쓰지 않는 레거시 wrapper·전용 테마·타입·CSS·테스트 fixture/설정을 정리한다. 현재 Bklit 생성 소스가 쓰는 하위 의존성은 구 wrapper와 구분하고 필요 경로를 기록해 보존한다. 남은 소비자가 있으면 그 패키지를 삭제하지 않고 전체 이관 미완료로 표시한다.
5. **의존성 제거:** 소비자가 0이면 프로젝트 package manager의 remove 명령으로 제거 대상 패키지를 삭제하고 lockfile을 갱신한다. 무관한 lockfile 재생성·major upgrade·공용 토큰 삭제는 하지 않는다.
6. **완료 증거:** 제거 대상별 `package.json`·lockfile 참조 0건과 실제 import/require/dynamic import·구 wrapper 사용 0건을 `rg`로 확인한다. 검색어는 인벤토리의 정확한 패키지/alias/경로로 만들고 앱·workspace·생성 소스를 포함한 검색 범위와 결과를 남긴다. `rg` exit `1`은 일치 없음이며 검색 오류를 0건으로 해석하지 않는다. 이후 typecheck/build/lint와 영향받는 tests·브라우저 parity를 재실행한다.

[data-surfaces.md](data-surfaces.md)의 계수 기준에 따라 레거시 import 0건은 앱 코드(page·component·wrapper·테마)에서 레거시 엔진 패키지와 그 wrapper를 import하는 파일이 0개라는 뜻이다. Bklit/shadcn이 생성한 chart source의 실제 하위 의존성 import는 레거시 계수에서 제외하고 경로를 기록한다. 구 Recharts wrapper는 Bklit 도입 이전에 프로젝트가 직접 작성한 recharts 기반 컴포넌트다. 화면 이관률 N/M은 고유 route 기준으로 계산한다. 파일·import 수는 별도로 기록한다. “실제 레거시 잔존 사용처”, “기록된 예외”, “미처리 이관 대상”을 구분하며, 미처리 이관 대상만 전체 대상−이관 완료−기록된 예외로 계산한다.

| 제거 대상 | 전체 사용 route·wrapper | 대상 이관/parity | 전체 이관 제안·사용자 결정 | manifest·lockfile·import 검색 명령/건수 | 실제 잔존/기록된 예외/미처리·재검토 조건 | 제거 후 typecheck/build·검증 |
|---|---|---|---|---|---|---|
| 실제 패키지·alias | 조사 범위 포함 | 증거 링크 | 승인/유예/예외 + 실제 근거 | 제거 완료이면 각각 0건 | 세 집계 각각 고유 route·수·이유 | 실제 결과·exit code |

공존은 과도기 또는 기록된 예외에만 허용한다. 대상 화면만 끝났으면 소유 참조의 “부분 적용: N/M 화면 이관, 나머지 제안 중” 형식으로 그 범위의 검증과 남은 전체 이관을 구분해 보고한다. 패키지 추가·wrapper 일부 수정만으로 전체 통일 완료를 주장하지 않는다.

## 외부 앱·계정 기능

Blender/Spline 같은 desktop 앱, Rive CLI/MCP, 생성 API는 npm 라이브러리와 별개다. [tool-capabilities.md](tool-capabilities.md)로 실제 사용 가능 기능을 정한 뒤 [graphics-production.md](graphics-production.md) 또는 필요한 [ai-assisted-3d.md](ai-assisted-3d.md)의 연결·작업 흐름을 실행한다. 연결 가능한 도구를 탐색하고 공식 배포·프로젝트 지침으로 설치한다. 사용자에게 터미널이나 모델링 작업을 넘기지 않는다. 로그인·GUI 권한처럼 에이전트가 할 수 없는 동작만 정확한 위치와 이유를 설명하고 완료 후 에이전트가 재개한다.

공식 근거: [Anime.js](https://animejs.com/documentation/getting-started/installation/), [Motion](https://motion.dev/docs/react-installation), [Bklit line chart](https://bklit.com/docs/components/line-chart), [R3F](https://r3f.docs.pmnd.rs/getting-started/installation).

단독 non-Git 산출물이면 Git 전용 설치 스크립트를 실행하지 않는다. 사용 가능한 도구와 native 인터뷰/시안 workflow를 사용한다: [standalone-visuals.md](standalone-visuals.md).
