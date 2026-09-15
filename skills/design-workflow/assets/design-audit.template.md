# Design audit

[project-audit.md](../references/project-audit.md)의 조사와 [verification.md](../references/verification.md)의 증거 형식을 따른다. `audit`는 대화 보고가 기본이며 사용자가 저장을 요청한 보고서에만 이 템플릿을 쓴다. source write·설치·issue/commit·정본 생성은 하지 않는다.

> Project:
> Mode: audit | new | rebrand | refactor | small-feature
> Baseline date:
> Routes/viewports:

## Product and current system

- Product job and primary purpose:
- Primary user and representative task:
- Existing design source and approved patterns:
- Stack/version/package manager/lockfile:
- Component/CSS/icon/font system, tokens/themes/breakpoints/navigation:
- Existing tests/Storybook/Playwright and documented commands:
- Inspection scope and unavailable evidence:

## Engine and library inventory

차트·표·모션 각각 실제 source·manifest·lockfile·실행 화면으로 확인한다. 없으면 조사 범위와 `없음`을 기록한다. registry 생성 source는 패키지 이름 없이 존재할 수 있다. 표는 headless 처리 로직과 시각 컴포넌트를, 모션은 package presence와 실제 제어 속성을 구분한다.

| Kind | Engine/library·version/source | Routes·imports/wrappers | Role·owned properties | Dependencies/registry evidence | Default alignment·migration/exception |
|---|---|---|---|---|---|
| Charts | Bklit 또는 레거시 실사용 | 전체 조사 route·alias | 차트 종류·데이터/기능 계약 | package.json·lockfile·components.json·생성 파일 | 대상 이관·전체 제안 필요 여부; 예외는 근거 |
| Tables | 기존 UI·headless logic | 표·폼·필터 사용처 | client/server sort/filter/page·편집 | 실제 source·lockfile | 보존·개선 범위 |
| Motion | Motion·Anime.js·기존 도구 | import·timeline·wrapper | 상태/layout/gesture·scroll/camera/속성별 소유자 | 실제 source·lockfile | 중복 제어·이관/예외 판정 |

차트의 화면 수는 고유 route로 집계하고 사용 파일/import 수와 구분한다. Bklit/shadcn 생성 chart source의 실제 하위 의존성은 레거시에서 제외하고 필요 경로를 기록한다. 구 Recharts wrapper는 Bklit 도입 이전에 프로젝트가 직접 작성한 recharts 기반 컴포넌트다. 레거시 잔존·기록된 예외·미처리 대상은 별도 집계한다.

`audit`는 인벤토리·판정·전체 이관 제안까지 대화로 보고하고 이관·설치·제거·기록 파일 생성은 하지 않는다. 사용자가 명시 요청한 보고서 저장만 이 템플릿 첫 문단의 경계를 따른다. 인벤토리의 제안은 사용자 승인이나 이관 완료가 아니다. 레거시 교체 규칙은 [data-surfaces.md](../references/data-surfaces.md)를 따른다.

## Evidence

모든 finding을 `observed`(직접 관찰), `detector`(자동 검사), `inferred`(확인 필요한 추론)로 분류한다. P0–P3와 함께 사용자 영향·수정 비용을 적는다. 기준선 문제와 새 회귀를 구분한다.

| ID | Type | Priority | Evidence | Scope | User impact | Correction cost / estimate basis | Recommendation | Regression risk |
|---|---|---|---|---|---|---|---|---|
| D-001 | observed/detector/inferred | P0–P3 | route/소스·조건·관찰·증거 | 영향 범위 | 과업 영향 | 수정 범위·예상 비용/시간·산정 근거·불확실성 | 수정 대상·기대 결과 | 보존 계약·회귀 검사 |

## Preserve

-

## Change

-

## Do not change

-

## Verification baseline

모든 모드에서 조사 범위의 검사와 공백을 기록한다. `audit`는 기존 결과·실행 화면·이미 사용 가능한 read-only detector만 사용한다. 표를 채우기 위해 build·설치·실제 데이터 변경을 실행하지 않는다. 없는 대상은 N/A와 근거, 실행할 수 없는 검사는 미실행과 이유다.

| 검사 | 명령/route | 조건(viewport·data·state·theme·auth) | 결과 | 미실행 사유 |
|---|---|---|---|---|
| lint |  |  |  |  |
| typecheck |  |  |  |  |
| related/full tests |  |  |  |  |
| build |  |  |  |  |
| source detector |  |  |  |  |
| rendered detector |  |  |  |  |
| desktop/mobile·320px/200% |  |  |  |  |
| representative task·states·permissions |  |  |  |  |
| keyboard/pointer·focus·reduced motion |  |  |  |  |
| design source·approved preview comparison |  |  |  |  |
| relevant work UI/chart/motion/graphics/3D checks |  |  |  |  |
| performance/runtime |  |  |  |  |

## Recommended first slice

- Target:
- Why, user impact and estimated correction cost:
- Acceptance criteria: user action → visible response → completion:
- Preservation and scope guard:
- Legacy migration proposal, remaining routes and decision needed if relevant:
- Evidence gaps and resulting limits on conclusions:
