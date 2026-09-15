---
name: design-workflow
description: Use for web UI, ERP, commerce and consumer sites, charts, dashboards, landing pages, AI-assisted 3D and interactive graphics, scroll video, game-like web experiences, redesigns and visual audits; also standalone decks and visual reports. Skip logic-only changes and ordinary tool explanations.
---

# Design Workflow

웹사이트를 사용하는 사람이 **목적을 이해하고, 필요한 정보를 찾고, 다음 행동을 쉽게 완료**하도록 설계한다. 시각 완성도는 정렬·타이포·정보 위계·일관성으로, 체감 품질은 즉각적인 피드백·안정된 레이아웃·명확한 상태·빠른 반응으로 만든다. 만족도 향상을 실측 없이 단정하지 않는다.

정본은 `ai-working/skills/design-workflow/`다. Claude/Codex가 같은 소스를 읽는다. 웹 개발을 기본 경로로 하고, 덱·시각 리포트는 요청 시 [standalone-visuals.md](references/standalone-visuals.md)를 추가로 읽는다. 일반 도구 설명이나 로직 전용 변경에는 디자인 게이트를 적용하지 않는다.

## 성능 원칙: 범위는 좁게, 강도는 전부

이 스킬의 기준은 효율이 아니라 **결과 품질·승인 정확도·검증 강도**다. 반복·장문은 허용하고 모순·누락·우회는 허용하지 않는다.

- 모드는 **범위와 write 권한**을 정하며 강도를 정하지 않는다. `small-feature`도 조사 항목, 공식 예제 관찰, 동작 시안 세 개(새 표현일 때), 검증 매트릭스를 `new`와 같은 강도로 수행한다. 좁아지는 것은 조사 **대상**(대상 화면 + 존재하는 인접 패턴 최대 두 개), 시안 **대상**(바뀌는 구간), 검증 **대상**(변경된 route·state)뿐이다.
- 어떤 단계를 생략하려 할 때는 "범위 밖"인지 "강도 축소"인지 먼저 구분한다. 범위 밖(예: 바뀌지 않는 화면의 시안, 바뀌지 않는 route의 Playwright)이면 생략하고 근거를 한 줄 남긴다. 강도 축소(예: 새 표현인데 시안 없이 구현, 반응형 범위인데 모바일 검증 생략, 레거시 엔진을 확인하지 않고 차트 수정)이면 생략하지 않는다.
- "간단히", "예쁘게만", "탭 하나만"은 범위 표현이다. 게이트·시안·검증의 면제 표현으로 해석하지 않는다.

## 작업 분류: 변경 모드와 사이트 목적

| 모드 | 기준 | 보존·승인 범위 |
|---|---|---|
| `new` | 새 제품·신규 랜딩 또는 재사용할 디자인 정체성이 없는 경우. 문서(`DESIGN.md`) 부재만으로 `new`로 전환하지 않는다. 기존 브랜드·토큰·컴포넌트를 디자인 근거로 확인할 수 있으면 변경 의도에 따라 보존형 `refactor` 또는 `small-feature` | 제품 인터뷰 → 디자인 방향 인터뷰 → 시각 방향 3개 선택 → 고해상도 시안 정확히 3개 승인 → 구현 잠금 해제 |
| `rebrand` | 브랜드·색·서체·톤 전면 변경 | `new`와 같은 5단계 게이트, 기존 기능·데이터 보존 |
| `refactor` | 기존 UI 구조·위계 개선 | 기존 정체성·동작 보존(보존형: scoped 게이트); 새 시각 세계관 또는 대표 화면 composition 전면 교체는 `new`의 5단계 게이트 |
| `small-feature` | 메뉴·모달·탭·폼·차트 하나·좁은 화면 변경 | 기존 토큰·컴포넌트 재사용, 전역 palette·typography 변경 금지. 조사·시안·검증의 **강도는 `new`와 동일**, **대상 범위**만 대상 화면·인접 패턴·관련 상태로 한정(scoped 게이트). 검증 순서(프로젝트 검사 → Source detector → Rendered detector → 브라우저 직접 조작 → 정본·목적별 대조)와 증거 형식은 전부 실행하고 대상 route·상태만 좁힌다 |
| `audit` | 진단·개선안만 요청 | 읽기 전용; source write·설치·issue/commit·정본 생성 금지, 대화로 보고 |

모호한 요청, 또는 scoped 모드(`small-feature`·보존형 `refactor`)의 범위 가드를 확인할 때 [mode-selection.md](references/mode-selection.md)를 읽는다. 기존 요청·답변·정본으로 확정 가능한 사실은 다시 묻지 않는다. 작은 작업을 새 제품 인터뷰로 확대하지 않는다.

모드와 별도로 [experience-routing.md](references/experience-routing.md)에서 **주 목적**을 고른다: 업무 UI, 커머스, B2C, 데이터 대시보드, 홍보·콘텐츠, 그래픽·3D 체험. 혼합 사이트는 페이지/구간별로 분류한다. 한 구간의 3D·모션 강도를 모든 페이지에 적용하지 않는다. 목적 선택은 시각 방향 승인을 대신하지 않는다.

## 도구 기본값과 레거시 교체 정책

### 기본 도구 선언

| 영역 | 기본 도구 | 레거시·대안 처리 | 상세 소유 참조 |
|---|---|---|---|
| 차트 | Bklit UI | ECharts·Chart.js·ApexCharts·Highcharts·nivo·Victory·Plotly·구 Recharts wrapper 등 레거시 엔진은 **교체 대상**. 비호환 판정 기준(비React / 프로젝트의 명시적 다른 엔진 계약 / 필수 기능 부재 / 대표 데이터 실측 성능 문제) 중 하나를 근거와 함께 기록한 경우만 예외. "명시적 계약"은 `AGENTS.md`/`CLAUDE.md`/`DESIGN.md` 또는 사용자 발화의 명시 결정만 뜻하며 기존 import의 존재는 계약이 아니다 | [data-surfaces.md](references/data-surfaces.md) |
| UI 상태·layout·gesture | Motion | 기존 `framer-motion`/`motion` 호환 버전을 재사용하고 중복 설치·무단 major upgrade 금지 | [motion-design.md](references/motion-design.md) |
| 연출·timeline(SVG·순차·복합) | Anime.js | 요청한 연출에 실제 연결. 같은 속성·scroll progress에 제어기 하나. GSAP은 Anime.js onScroll/Motion useScroll로 구현 불가한 기능을 공식 문서·실측으로 확인하고 DESIGN에 예외로 기록한 경우에만 추가한다 | [motion-design.md](references/motion-design.md), [motion-and-3d.md](references/motion-and-3d.md) |
| 3D | Three.js; React는 R3F(+Drei); 단순 회전·색상·AR은 model-viewer 조건부 | Spline 등은 export·runtime 조건을 확인한 뒤 선택 | [motion-and-3d.md](references/motion-and-3d.md), [ai-assisted-3d.md](references/ai-assisted-3d.md) |
| 그래픽 영상·scroll media·2D/2.5D·게임형 | 전달 경로를 비교해 선택 | 혼합형은 후보이지 기본값이 아님 | [graphics-production.md](references/graphics-production.md) |
| 디자인 보조 스킬 | Taste Skill + Impeccable | 설치하지 않아도 native로 같은 게이트·검증 수행 | [tooling.md](references/tooling.md) |

### 요청별 실행 규칙

| 요청/대상 | 실행 규칙 | 필요한 참조 |
|---|---|---|
| 웹 UI 작성·수정 | Motion을 기본 도구로 상태·전환을 설계한다. 새 모션 방향은 실제 동작 시안 세 개로 고르고 승인된 패턴은 재사용한다 | [motion-design.md](references/motion-design.md) |
| 업무 UI(ERP·관리자): 표·폼·필터·키보드 입력·밀도·숫자·권한별 상태 | 표(열 정렬·고정 헤더/열·행 높이·인라인 편집·정렬/필터/페이지 상태), 폼(라벨·그룹·오류 위치·저장 상태), 필터바, 키보드 중심 입력, 밀도, 숫자 정렬·단위, 권한별 상태를 전용 참조 기준으로 설계·검증한다. 상태 전환은 Motion, 차트는 Bklit 경로를 함께 적용한다 | [work-ui-surfaces.md](references/work-ui-surfaces.md) + [web-quality.md](references/web-quality.md) |
| 애니메이션·인터랙션 연출 추가 | Anime.js 설치·버전·기존 사용을 확인하고 요청한 연출에 연결한다. 없으면 로컬 설치하며 Motion과 대상 속성을 나눈다 | motion design + [tooling.md](references/tooling.md) |
| 차트 작성·디자인 변경 | Bklit UI를 기본 경로로 적용하고 새 표현은 같은 데이터의 동작 시안 세 개로 선택한다. 레거시 엔진이 있으면 아래 교체 정책을 적용한다 | [data-surfaces.md](references/data-surfaces.md) |
| 느낌·연출 명칭을 모르거나 요청이 모호함 | 시스템·도메인 분석으로 쉬운 경험 이름·추천 이유·보완 요청문을 선제안한다. 충분히 명확하면 생략한다 | [intent-to-experience.md](references/intent-to-experience.md) |
| 그래픽 영상·scroll media·입자·게임형·혼합형 웹 | 원하는 조작을 기준으로 제작/전달 경로를 비교하고 AI가 장면 제작부터 실제 웹 연결까지 맡는다 | [graphics-production.md](references/graphics-production.md) |
| 3D 웹 제작, 모델링 경험 없음 | AI가 모델 확보·제작·수정·시각 검수·export·웹 통합을 맡는다. 사용자는 원하는 모습과 정확도를 판단한다 | [ai-assisted-3d.md](references/ai-assisted-3d.md) |
| 외부 서비스/프리미엄 기능 사용 | 서비스별 실제 free/paid 권한으로 제작부터 전달까지 가능한 경로를 선택한다 | [tool-capabilities.md](references/tool-capabilities.md) |

### 레거시 차트 엔진 교체 정책(요지)

절차·예외 판정·완료 증거 표의 정본은 [data-surfaces.md](references/data-surfaces.md)의 `## 레거시 차트 엔진 교체` 절, parity 검증 절차는 [verification.md](references/verification.md)의 `## 레거시 차트 엔진 교체 parity 검증`, 패키지 제거 절차는 [tooling.md](references/tooling.md)의 `## 레거시 차트 엔진 제거 절차`다. 요지는 다음과 같다.

1. **인벤토리**: 조사 단계에서 [project-audit.md](references/project-audit.md)의 차트 엔진 인벤토리로 프로젝트 전체의 레거시 엔진·사용처·공통 wrapper를 표로 기록한다. 인벤토리 없이 차트를 수정하지 않는다. `new`는 기준선 화면이 없으므로 대상 화면 이관·parity는 N/A이지만, 같은 저장소에 레거시 엔진이 있으면 인벤토리·판정·전체 이관 제안·공존 기록은 그대로 적용한다. `audit`는 인벤토리·판정·전체 이관 제안까지 대화로 보고하고, 이관·설치·제거·기록 파일 생성은 하지 않는다.
2. **판정**: React/shadcn 호환이면 Bklit 이관이 기본. 호환은 React이고 shadcn components.json·Tailwind 기반 chart source를 기존 CSS 체계와 충돌 없이 추가할 수 있는 경우다. 도입이 필요하면 도입 diff·영향 범위·토큰 매핑을 제시하고 그 도입 결정 하나만 받는다(승인=Bklit 기본, 거부=예외 2 기록). 정의는 data-surfaces.md 2. 판정. 비호환 예외 네 기준 중 하나를 근거와 함께 기록한 경우만 유지한다. "기존에 쓰고 있다", "다른 화면이 아직 레거시다", "일정이 촉박하다"는 유지 사유가 아니다. 레거시 차트를 "스타일만 손보는" 선택지는 만들지 않는다.
3. **대상 화면 이관**: 이번 범위의 차트를 Bklit로 구현한다(새 표현이면 동작 시안 세 개). 확인된 개별 차트 예외가 없는 화면은 모든 레거시 차트를 함께 이관한다. 개별 차트의 비호환 예외(필수 기능 부재·실측 성능)가 기록된 화면은 해당 차트에 한해 공존을 허용하고, 예외 범위·의존 비용·재검토 조건을 기록한다. 해당 route는 `기록된 예외`로 집계하며 `이관 완료`나 레거시 import 0건으로 표시하지 않는다. 따라서 요청이 "차트 하나"여도 같은 화면의 다른 레거시 차트는 이번 범위이며, 승인된 표현이 있으면 재사용하고 새 표현이면 같은 세 시안 안에 포함한다. 개별 차트 예외가 없는 대상 화면의 레거시 import는 0건이어야 한다(계수 단위는 data-surfaces.md: 앱 코드가 레거시 패키지·구 wrapper를 import하는 파일 수, Bklit 생성 소스의 하위 의존성은 제외).
4. **동일 데이터 parity 검증**: 같은 route·필터·기간·데이터·theme·viewport·auth로 이전 엔진과 대조한다(수치·필터/기간·tooltip·범례·export·상태·키보드/터치·모바일).
5. **전체 이관 제안**: 인벤토리에 근거해 남은 화면의 범위·순서·예상 회귀·필요한 결정을 완료 보고에 포함해 제시한다. 승인 없이 대상 화면 밖의 차트를 바꾸지 않으며, 제안을 생략하지도 않는다.
6. **승인 시 이관과 제거**: 승인된 범위·순서대로 화면별로 3~4를 반복하고, 마지막 사용처가 사라진 뒤 패키지·wrapper·테마·타입을 제거하고 build/lint/test를 실행한다.
7. **완료 증거**: 완료 증거 표(화면별 이전/이후 엔진·레거시 import 건수·parity 결과·제거 파일·상태)와 **남은 사용처 수**, 다음 이관 범위를 기록한다. 인벤토리의 모든 행이 `이관 완료` 또는 `기록된 예외`가 되기 전에는 완료가 아니며, 과도기 보고는 반드시 **"부분 적용: N/M 화면 이관, 나머지 제안 중"** 형식이다. N·M은 **고유 route(화면) 기준**이다: M = 인벤토리의 화면/route 행 수, N = `이관 완료` 행 수. 파일·import 수는 별도로 기록한다. 잔여는 **실제 레거시 잔존 사용처**(레거시가 남은 모든 화면), **기록된 예외**, **미처리 이관 대상**(= 전체 대상 − 이관 완료 − 기록된 예외)의 세 값으로 구분해 적는다.

두 엔진의 공존은 **과도기**(이관 진행 중이며 실제 레거시 잔존 사용처·기록된 예외·미처리 이관 대상·다음 이관 범위가 기록됨) 또는 **기록된 비호환 예외**(화면 단위 또는 위 3의 개별 차트 예외)에만 허용한다. 장기 상태로 두지 않는다. 비호환 판정이면 프레임워크를 이관하지 않고 대안과 필요한 결정 하나를 제시한다.

### 공통 원칙

사용자의 명시 선택·프로젝트의 강제 계약이 우선이다(이 우선순위는 **도구 선택에 한하며** 게이트·동작 시안·검증을 면제하지 않는다; 면제 요청의 처리는 `### 사용자 메시지 해석표`). 비호환 framework, 필요한 기능 부재, 실측 성능 문제는 근거와 대안을 제시한다. 기존 의존성이 없거나 작업이 ERP라는 이유로 기본 모션·차트 경로를 생략하지 않는다. 도구 사용을 위해 framework를 이관하거나 사용하지 않는 패키지를 설치하지 않는다. `audit`는 계속 읽기 전용이며 정적 덱에는 앱 모션 패키지를 강제하지 않는다.

새 차트·모션·그래픽·3D 방향을 제작할 때는 해당 소유 참조의 **공식 실행 예제 직접 관찰 → 채택할 표현 지정 → 같은 데이터/콘텐츠로 동작 시안 정확히 세 개 → 결과 대조**를 따른다. 정지 이미지·외부 링크만으로 대체하지 않는다. 이 확인은 기존 시안 과정에 포함하며 별도 인터뷰·승인 단계나 추가 시안 묶음을 만들지 않는다. 승인된 패턴의 작은 수정은 기존 근거를 재사용한다.

**공식 예제 직접 관찰의 완료 조건**: 접근 가능한 공식 실행본(예제 페이지·playground) 또는 공식 소스로 로컬에 띄운 예제를 브라우저에서 **직접 조작**(클릭·hover·필터·스크롤·재생)하고 URL·확인한 행동·보이는 결과를 기록했을 때만 완료다. 문서·영상·소스 읽기·설치 성공은 준비 자료이며 관찰 완료로 처리하지 않는다. 직접 관찰이 미완료이면 새 방향의 최종 채택과 application source 구현을 보류한다. 접근 가능한 실행본이 있으면 결정을 묻지 않고 직접 조작한다. 접근 불가(URL 응답 실패·로컬 실행 실패의 실제 근거)가 확인된 경우에만 사용자에게 접근 가능한 공식 실행본 확보·공식 소스의 로컬 실행·해당 방향 보류 중 하나를 결정받는다. 대체 자료와 진행 요청은 직접 관찰 완료를 대신하지 않는다. 세 선택지 중 관찰 없이 채택하는 경로는 없다: 실행본 확보·로컬 실행은 관찰을 완료한 뒤에야 채택으로 이어지고, 방향 보류는 그 방향을 시안·구현에서 제외한다. 접근 불가 상태는 그 제약과 실제 확인한 대체 근거(공식 영상·문서·소스)를 구분해 기록하고 "직접 관찰 미완료"로 표시한다. 이 문장은 data-surfaces·motion-design·graphics-production·ai-assisted-3d·verification·템플릿이 같은 문구로 반복한다.

**동작 시안의 개수**: 새 표현이 들어가는 구간은 `new`든 scoped 작업이든 모션·차트·그래픽·3D 모두 같은 콘텐츠·대표 행동으로 **동작 시안 정확히 세 개**를 만든다. 신규 디자인에서는 세 composition 안에 통합하고, scoped 작업에서는 바뀌는 구간만 세 개로 비교한다. 영역마다 세 개 묶음을 따로 만들지 않고, 한 구간에 모션·차트가 함께 있으면 같은 세 시안 안에서 비교한다.

**승인된 패턴의 정의**: DESIGN.md·구현노트·gate 기록에 **사용자 결정이 남아 있는** 패턴만 승인된 패턴이다. 기록 없는 기존 코드 패턴은 재사용할 수 있지만 "승인됨"으로 기록하지 않고, 그 패턴을 적용한 결과가 새 표현인지를 아래 판정으로 정한다. 새 표현이면 동작 시안 세 개와 사용자 결정, 아니면 "기존 코드 패턴 재사용(미승인, 사용자 결정 기록 없음)"으로 적고 원 코드 위치·동작 동일성·새 표현이 아니라는 판정 근거·변경 상태 검증을 연결한다. 이 세 번째 분기(승인 패턴 재사용 / 기존 코드 패턴 재사용(미승인) / 새 표현)는 gate template과 DESIGN의 Motion·Charts 필드에도 같은 이름으로 있다.

**새 표현 판정**: 같은 컴포넌트 유형에 같은 동작(구조·순서·타이밍 범위)이 이미 운영 화면에 있고 바뀌는 것이 엔진·구현뿐이면 새 표현이 아니다. 동작·구조·강조 방식이 하나라도 바뀌면 새 표현이다. 재사용이면 재사용 근거를 기록한다. 예: CSS transition 탭을 같은 indicator 이동·같은 타이밍 범위로 Motion에 재구현 → 새 표현 아님; 탭 전환에 없던 패널 slide·공유 요소 이동을 추가 → 새 표현. ECharts 선 차트를 같은 정보 위계·같은 tooltip 동작으로 Bklit에 재구현 → 새 표현 아님; KPI 연동 hover·기간 brush를 추가 → 새 표현. 판정 결과와 근거는 gate template의 해당 `Relevant experience evidence` 행에 적는다.

사용자가 방향을 선택한 뒤에는 승인된 시안·토큰·상태 동작을 프로젝트의 기준선으로 삼아 필요한 부분을 보강한다. 다른 차트 종류나 화면으로 확장할 때도 이 기준선을 먼저 적용하며, 승인된 표현과 새로 결정할 표현을 구분한다. 상세 재사용·확장 기준은 [data-surfaces.md](references/data-surfaces.md)를 따른다.

## 규칙 소유

같은 규칙을 여러 파일이 반복 서술할 수 있다. 반복 서술은 아래 소유 파일과 **같은 숫자·순서·용어**여야 하며, 충돌하면 소유 파일이 우선한다. 새 규칙·새 목적·새 도구는 소유 파일에 먼저 쓰고 SKILL.md에는 요지와 링크만 둔다. 소유 파일이 없는 새 주제는 이 표에 행을 추가한 뒤 파일을 만든다.

| 규칙 | 소유 파일 |
|---|---|
| 변경 모드 5개의 정의·보존 범위 | SKILL.md `## 작업 분류`; 모호 사례·모드별 범위 가드는 [mode-selection.md](references/mode-selection.md) |
| 주 목적 6개와 참조 라우팅 | [experience-routing.md](references/experience-routing.md) |
| 절대 게이트 5단계, 승인의 정의, `ㄱㄱ`/위임/요약 확인/부분 승인/subagent 처리, 사용자 발화·질문·추천·채택의 기록 위치 규칙, 게이트 정지 형식 | SKILL.md `## 신규·리브랜딩 절대 게이트` |
| 고해상도 시안 정확히 세 개·서로 다른 composition | SKILL.md `## 신규·리브랜딩 절대 게이트` |
| `audit` 읽기 전용 경계 | SKILL.md `## 작업 분류`; 조사 범위는 [project-audit.md](references/project-audit.md) |
| 도구 기본값 선언(Bklit / Motion / Anime.js / Three.js·R3F / Taste Skill + Impeccable) | SKILL.md `## 도구 기본값과 레거시 교체 정책`; 설치·연결 절차는 [tooling.md](references/tooling.md) |
| 속성 소유권(같은 scroll progress·camera·속성에 제어기 하나) | [motion-design.md](references/motion-design.md) `## 구현 계약`, 3D는 [motion-and-3d.md](references/motion-and-3d.md) |
| 공식 예제 관찰의 완료 조건·동작 시안 개수(정확히 세 개)·승인된 패턴의 정의 | SKILL.md `## 도구 기본값과 레거시 교체 정책` `### 공통 원칙` |
| 공식 예제 관찰 → 채택 표현 → 동작 시안 3 → 대조의 영역별 절차 | 차트 [data-surfaces.md](references/data-surfaces.md), 모션 [motion-design.md](references/motion-design.md), 그래픽 [graphics-production.md](references/graphics-production.md), 3D [ai-assisted-3d.md](references/ai-assisted-3d.md) |
| 모션 선택·과업별 추천·timing/easing·Motion/Anime.js 역할 분담 | [motion-design.md](references/motion-design.md) |
| 3D runtime·scroll 연결·자산 최적화·성능 검증 | [motion-and-3d.md](references/motion-and-3d.md) |
| 그래픽 전달 경로(영상·scroll media·2D/2.5D·실시간·게임형·혼합) 비교와 검증 | [graphics-production.md](references/graphics-production.md) |
| 3D 모델 확보·제작·검수·export·웹 연동 | [ai-assisted-3d.md](references/ai-assisted-3d.md) |
| 차트 기본 경로·재사용/확장·호환성 대안 | [data-surfaces.md](references/data-surfaces.md) |
| 레거시 차트 엔진 교체 절차·비호환 예외 판정 | [data-surfaces.md](references/data-surfaces.md) `## 레거시 차트 엔진 교체` |
| 레거시 교체 완료 증거 표·남은 사용처 수 기록 | [data-surfaces.md](references/data-surfaces.md) `## 레거시 차트 엔진 교체` |
| 레거시 parity 실행 절차·검사표(같은 데이터로 구·신 차트 대조) | [verification.md](references/verification.md) |
| 업무 UI 표·폼·필터·키보드·밀도·숫자·권한 설계·검증 항목 | [work-ui-surfaces.md](references/work-ui-surfaces.md) |
| 업무 UI 모션 패턴(탭·행 펼침·저장 상태 등 과업별 추천) | [motion-design.md](references/motion-design.md) |
| 보조 스킬·앱 라이브러리의 설치 버전·모드별 Taste Skill 매핑·설치 스크립트 옵션 | [tooling.md](references/tooling.md) |
| 웹 품질 기준(정렬·가독성·조작·반응형·성능) | [web-quality.md](references/web-quality.md) |
| 검증 매트릭스·명령·증거 형식 | [verification.md](references/verification.md) |
| 불만족 피드백 절차·스킬 반영 조건 | [feedback-improvement.md](references/feedback-improvement.md) |
| 외부 서비스 무료/유료 기능 판정 | [tool-capabilities.md](references/tool-capabilities.md) |
| 조사 read order·정적/시각/런타임 인벤토리 | [project-audit.md](references/project-audit.md) |
| PRODUCT/DESIGN 정본의 기록 항목 | [design-context.md](references/design-context.md); 필드는 [PRODUCT](assets/PRODUCT.template.md)·[DESIGN](assets/DESIGN.template.md) 템플릿 |
| 의도 구체화(쉬운 경험 이름·보완 요청문) | [intent-to-experience.md](references/intent-to-experience.md) |
| 덱·제안서·시각 리포트 | [standalone-visuals.md](references/standalone-visuals.md) |
| 게이트 증거 기록 필드 | [design-gates.template.md](assets/design-gates.template.md) |
| 감사 보고 필드 | [design-audit.template.md](assets/design-audit.template.md) |

새 **주 목적**을 추가하면 다음 여덟 곳을 함께 고친다: (1) [experience-routing.md](references/experience-routing.md) `## 주 목적` 표, (2) SKILL.md `## 작업 분류`의 목적 목록, (3) [PRODUCT 템플릿](assets/PRODUCT.template.md)의 `Primary website purpose`, (4) [gate 템플릿](assets/design-gates.template.md)의 `Primary purpose and scope`, (5) [DESIGN 템플릿](assets/DESIGN.template.md)의 `Primary purpose and affected routes/sections` 목적 열거, (6) 전용 참조, (7) [verification.md](references/verification.md)의 목적별 검증 항목, (8) [design-context.md](references/design-context.md)의 대응 필드·기록 기준·목적 열거·필드 개수. 새 **도구**를 추가하면 다음 일곱 곳을 함께 고친다: (1) SKILL.md 도구 선언 표, (2) [tooling.md](references/tooling.md) 설치 표, (3) 해당 목적 참조, (4) [DESIGN 템플릿](assets/DESIGN.template.md)의 결정 필드, (5) [gate 템플릿](assets/design-gates.template.md)의 `Relevant experience evidence` 행, (6) [verification.md](references/verification.md)의 검증 항목, (7) [design-context.md](references/design-context.md)의 대응 필드·기록 기준·목적 열거·필드 개수. [experience-routing.md](references/experience-routing.md) `## 소유 규칙`은 같은 목록을 같은 순서로 반복한다. 하나라도 빠지면 추가를 완료로 보지 않는다. 위 목록에 없는 파일(예: mode-selection·intent-to-experience·standalone-visuals·web-quality)은 새 목적·도구를 본문에 다시 정의하지 않고 소유 파일 링크로만 가리킨다; 그 파일이 이미 목적·도구 이름을 열거하고 있으면 열거만 같은 이름으로 갱신한다.

## 신규·리브랜딩 절대 게이트

`new`, `rebrand`, 시각 세계관 교체 또는 대표 화면 전면 교체형 `refactor`는 다음 순서를 지킨다.

1. **제품 인터뷰**: 사용자·핵심 과업·차별점·성공/실패 기준을 한 질문씩 확인한다. 새 `PRODUCT.md`를 쓰기 전에 실제 사용자 답변을 최소 한 번 받는다. 저장소 증거로 추정 가능한 항목은 **항목별 값·추정 근거를 열거한 요약 확인 라운드** 하나로 묶어 확인받을 수 있으며, 그 라운드는 "질문 하나"로 센다(처리는 `### 사용자 메시지 해석표`의 요약 확인 행). 값·근거를 열거하지 않은 요약("이 정도로 이해했는데 맞나요?")은 요약 확인 라운드가 아니다.
2. **디자인 방향 인터뷰**: 브랜드 성격, reference/anti-reference, 밀도, 우선 platform, 접근성 목표를 확인한다. "생각한 디자인 없음"도 생략 사유가 아니다.
3. **시각 방향 세 개**: 이름·핵심 장면·palette·typography·layout 원리가 다른 방향을 제시한다. 사용자의 선택 또는 선택지를 본 뒤의 명시적 위임을 기다린다.
4. **고해상도 시안 정확히 세 개**: 선택된 방향 안에서 composition·density·hierarchy가 다른 시안을 함께 보여주고 `승인 / 조합 / 수정 / 폐기` 결정을 받는다. 같은 레이아웃의 색상 변경만으로 세 개를 채우지 않는다.
5. **구현 잠금 해제**: 선택·채택/비채택 요소·승인 근거를 [gate template](assets/design-gates.template.md)에 기록한 뒤 application source를 수정한다.

`small-feature`와 보존형 `refactor`는 1·2·3·4를 `N/A`(근거 포함)로 표시하는 scoped 게이트를 쓴다. 단 새 모션·차트·그래픽 표현이 들어가면 그 구간의 동작 시안 세 개와 사용자 결정은 scoped 게이트 안에서 그대로 필요하다. `audit`는 게이트 파일을 만들지 않고 잠금 상태를 유지한다.

**잠금 해제 전 기록과 구현 후 갱신의 구분**(full·scoped 공통): 잠금 해제 전에는 인벤토리·범위·예외 판정·시안 결정·실행 계획을 기록한다. 실제 이관·parity·제거·변경 후 검증과 완료 보고 시 받을 전체 이관 결정은 `구현 후 갱신 예정`으로 표시하며 초기 잠금 해제 조건에 포함하지 않는다. 해당 결과는 완료 판정 전에 갱신한다. 판정: gate template의 `Legacy chart engine migration`·`Work UI evidence`·`Verification evidence`에서 구현이 있어야 채워지는 값이 비어 있다는 이유로 잠금 해제를 미루지 않고, 반대로 그 값이 `구현 후 갱신 예정`인 채로 완료를 보고하지 않는다.

### 승인의 정의

승인은 **사용자가 해당 단계의 선택지·산출물을 본 뒤에 보낸 명시적 메시지**다. 다음 세 조건이 모두 맞아야 한다.

1. 메시지가 그 산출물(방향 세 개, 시안 세 개, 조합/수정안)을 제시한 **이후**에 왔다.
2. 메시지의 내용이 그 산출물에 대한 결정(`선택`, `승인`, `조합`, `수정`, `폐기`, 또는 명시적 위임)으로 읽힌다.
3. 메시지를 보낸 주체가 사용자다. 모델·reviewer·subagent·다른 에이전트의 메시지는 승인이 아니다.

**선택지를 본 뒤의 명시적 위임**은 다음 발화다: 방향 세 개 또는 시안 세 개를 제시(방향: 이름·핵심 장면·palette·typography 설명 또는 이미지; 시안: 로컬 서버 응답을 확인한 URL, 움직이는 요소가 없는 정적 화면만 이미지 허용)하고 AI 추천안을 명시한 **뒤에**, 사용자가 "네가 골라", "추천안으로", "알아서 해", "ㄱㄱ"처럼 선택을 에이전트에게 맡기는 메시지를 보낸 경우. 예: 시안 URL 세 개와 "추천: B(정보 밀도가 과업에 맞음)"를 보낸 다음 턴에 사용자가 "네가 골라" → B를 채택한 위임으로 기록한다. **보기 전 위임은 무효다**: 산출물을 제시하기 전에 온 "알아서", "네가 정해", "ㄱㄱ"는 착수 승인일 뿐이며, 제시 후 같은 말을 다시 받아야 위임이 성립한다. 제시 후라도 AI 추천안이 없었으면 추천안을 붙여 한 번 더 묻는다.

### 사용자 메시지 해석표

**기록 위치 규칙(모든 행 공통)**: 질문과 AI 추천은 `Question`(또는 해당 절의 AI recommendation 필드)에, 사용자 발화는 `Real user answer`(절에 따라 `Real user answer or explicit summary approval`, `User choice, or explicit delegation after viewing`, `Real user answer, or explicit delegation after viewing`)에 **원문 그대로**, 채택 결과는 해당 `Confirmed …`/`Adopt` 필드에 기록한다. 사용자 발화 필드에 질문·추천·요약·채택안을 섞어 쓰지 않는다. 요약 확인의 제시문 원문도 `Question`에 둔다. 시각 방향·시안 절의 채택 필드는 둘 다 `Adopt`다.

| 사용자 메시지 | 시점 | 처리 |
|---|---|---|
| `ㄱㄱ`, `진행`, `고`, `ok`, `알아서`, `네가 정해`, `추천대로` | 해당 단계가 존재하고 그 선택지·시안을 **아직 보여주지 않음** | **착수 승인**으로만 처리한다(작업을 시작해도 된다). 방향·시안의 승인이 아니다. application source write는 잠금 유지. 인터뷰 항목이 비었으면 아래 게이트 정지 형식으로 질문 하나를 내고, 인터뷰가 채워졌으면 미제시 게이트 산출물을 만들어 제시한다(scoped 작업에서 새 표현이 없으면 해당 단계가 없으므로 scoped 게이트 기록 후 해제). 직전 턴이 AI 추천을 붙인 인터뷰 질문이면 이 행이 아니라 다음 행을, 항목별 값·추정 근거를 열거한 요약 확인 라운드이면 그다음 행을 적용한다 |
| `ㄱㄱ`, `추천대로`, `그렇게`, `네` | 인터뷰(1·2단계) 질문 하나를 **AI 추천과 함께** 제시한 직후 | 이 행이 첫 행보다 우선한다. **그 질문 하나의 답**으로 추천안을 채택한다. 기록 위치 규칙대로 질문은 `Question`, 추천은 해당 절의 AI recommendation 필드, 사용자 메시지 원문은 `Real user answer`, 채택한 값은 `Confirmed …`에 적는다. 다른 빈 항목의 답이 아니며 방향·시안의 승인도 아니다. 다음 빈 항목이 있으면 다시 질문 하나(추천 포함), 없으면 미제시 산출물을 제시한다. 추천 없이 낸 질문 뒤의 `ㄱㄱ`는 답이 아니므로 추천을 붙여 한 번 더 묻는다 |
| `네`, `맞아`, `ㄱㄱ` | 저장소 증거로 추정한 인터뷰(1·2단계) 항목을 **항목별 값·추정 근거를 열거한 요약 확인 라운드**로 제시한 직후 | 요약에 열거된 항목 **전부**의 확인으로 처리하고, 요약 원문은 `Question`, 사용자 원문은 `Real user answer`(제품 인터뷰 절은 `Real user answer or explicit summary approval`), 확인된 값은 `Confirmed …`에 기록한다. 열거되지 않은 항목·"추정 불가"로 표시한 항목의 답이 아니므로 그 항목은 질문 하나로 이어간다. 방향·시안의 승인이 아니다. 요약이 항목별 값·추정 근거를 열거하지 않았으면 이 행이 아니라 바로 위 행(질문 하나)으로 처리한다: 요약이 실제로 물은 항목 하나의 답으로만 채우고(추천이 없었으면 추천을 붙여 한 번 더 묻는다) 나머지 항목은 질문 하나씩 이어간다 |
| `시안 없이 바로 구현해`, `게이트 생략하고 진행`, `인터뷰 필요 없어` | 어느 시점이든 | **면제가 아니다.** 절대 게이트·scoped 동작 시안은 사용자 요청으로 생략되지 않는다. 이유(승인 정확도·재작업 비용)를 한 줄로 알리고 게이트 정지 형식으로 이번 산출물을 제시한다. scoped 작업에서 새 표현 없이 승인 패턴 또는 (새 표현 판정에 따른) 기존 코드 패턴을 재사용하면 **동작 시안만** 생략한다. 승인 여부·재사용 근거(승인 패턴 이름·기록 위치, 또는 원 코드·동작 동일성·판정 근거)·보존 범위·신규 전용 항목의 N/A를 gate template에 기록하고 구현 잠금을 해제한다. full 게이트는 이 분기로 생략하지 않는다 |
| `ㄱㄱ`, `진행`, `알아서`, `추천대로`, `네가 골라` | 선택지·시안을 **보여준 직후**, 제시문에 **AI 추천안이 명시**돼 있음 | **선택지를 본 뒤의 명시적 위임**으로 처리한다. 추천안을 채택하고 기록 위치 규칙대로 gate template에 적는다: 방향이면 추천은 `AI recommendation and reason shown with the options`, 사용자 원문은 `User choice, or explicit delegation after viewing`, 채택한 방향은 `Adopt`; 시안이면 추천은 `AI recommendation and reason`, `User decision: approve`, 사용자 원문은 `Real user answer, or explicit delegation after viewing`, 채택안은 `Adopt`, 제시 시점·URL·추천·원문 시점은 `Delegation after viewing stage 4` |
| 같은 표현 | 선택지·시안을 보여준 직후, 제시문에 AI 추천안이 **없음** | 위임으로 처리하지 않는다. 추천안 하나와 이유를 붙여 "A/B/C 중 선택 또는 추천안(B)으로 진행" 형식으로 한 번 더 묻는다 |
| `A`, `B로`, `2번` | 선택지·시안을 보여준 뒤 | 해당 항목의 승인. 사용자 원문은 사용자 발화 필드(방향 `User choice, or explicit delegation after viewing` / 시안 `Real user answer, or explicit delegation after viewing`), 채택안은 `Adopt` |
| `승인` | 선택지·시안을 보여준 뒤 | `승인`만으로 대상이 유일하게 특정되는 경우(안이 하나 남았거나 직전에 특정 안을 재제시)에만 해당 안을 승인 처리한다. AI 추천안이 명시된 뒤의 `승인`·`추천대로`는 추천안 승인이다(`추천대로`는 위의 위임 행 형식으로 `Delegation after viewing stage 4`까지 기록한다). 여러 안이 남았고 추천안도 명시되지 않아 채택 대상이 불명확하면 승인할 안 하나를 확인하며 잠금을 유지한다(추천안 하나와 이유를 붙여 "A/B/C 중 어느 안의 승인인지"를 묻는다). 세 안 전체의 승인으로 해석하지 않는다 |
| `A 레이아웃에 B 카드`, `B인데 헤더 작게` | 시안을 보여준 뒤 | **부분 승인**(`조합`/`수정`). 아래 재제시 규칙 적용 |
| `다 별로`, `폐기` | 시안을 보여준 뒤 | `폐기`. 같은 방향에서 composition이 다른 새 시안 세 개를 만들거나, 방향 자체를 다시 묻는다 |
| 이전 세션·이전 작업의 `ㄱㄱ`·승인 | 이번 산출물 제시 전 | 이번 산출물의 승인이 아니다. 기존 승인 범위(승인된 정본·패턴)만 재사용한다 |
| 승인 뒤 "여백 조금 더", "색 한 단계 진하게" 등 승인된 시안·토큰·상태 동작의 범위 안에서 새 시각 방향이나 미승인 핵심 동작을 추가하지 않는 수정 | 잠금 해제 후 | 재승인하지 않고 반영한다. 범위를 넘는 변경(새 구간·새 표현·새 세계관·미승인 핵심 동작)은 해당 부분만 새 선택으로 다룬다 |

### 부분 승인과 재제시

- `조합` 또는 `수정`을 받으면 그 결과를 **하나의 시안**으로 만들어 다시 보여주고 `승인`을 받은 뒤 잠금을 해제한다. 재제시에는 세 개 규칙을 적용하지 않는다(조합/수정안 하나 + 필요 시 비교용 원안).
- 재제시 뒤 다시 `수정`이 오면 같은 절차를 반복한다. 반복 횟수 제한은 없지만, 매 회 실제 산출물을 보여준 뒤 결정을 받는다. 보여주지 않은 수정안을 "반영했다"로 처리하지 않는다.
- 조합/수정안에 새 구간·새 표현(예: 없던 차트, 새 모션 방향)이 들어가면 그 부분은 새 표현으로 취급해 해당 소유 참조의 동작 시안 규칙을 따른다.
- 승인 범위는 마지막으로 보여주고 승인받은 산출물에 한정한다. 잠금 해제 후, 승인된 시안·토큰·상태 동작의 범위 안에서 새 시각 방향이나 미승인 핵심 동작을 추가하지 않는 수정에는 같은 승인을 재요청하지 않는다. 범위를 넘는 변경은 해당 부분만 새 선택으로 다뤄 다시 보여주고 결정을 받는다.

### subagent·reviewer의 권한

- 할 수 있는 것: 조사, 시안 제작, 비평, 검증 실행, 결함 보고, 추천안 제안.
- 할 수 없는 것: gate template의 `Status: complete`·사용자 발화 필드(`Real user answer …`/`User choice …`)·`User decision`·`Adopt` 채우기, 사용자 메시지를 승인으로 해석하기, `Implementation unlocked: yes` 기록, 사용자 대신 선택하기.
- gate template의 사용자 답변 필드에는 **사용자 메시지 원문**만 넣는다(질문·추천·채택 결과의 기록 위치는 `### 사용자 메시지 해석표`의 기록 위치 규칙). subagent에게 전달된 지시문·요약은 원문이 아니다. 여러 에이전트가 일하면 사용자와 직접 대화하는 에이전트만 승인을 기록한다.
- reviewer가 "승인해도 될 것 같다"고 해도 사용자의 메시지가 없으면 잠금을 해제하지 않는다.

### 게이트 정지 형식

필수 게이트가 비어 있거나 승인 조건이 맞지 않으면 application source write를 멈추고, **누락된 게이트의 산출물 하나**를 제시한다. 산출물은 게이트에 따라 다르다: 1·2단계가 비면 **질문 하나**(저장소 증거로 추정한 항목이 여러 개면 항목별 값·추정 근거를 열거한 요약 확인 라운드도 질문 하나로 센다), 3단계가 비면 **시각 방향 세 개**, 4단계가 비면 **고해상도 시안 세 개**, scoped 작업에서 새 표현의 동작 시안이 비면 **동작 시안 세 개**, 조합/수정 뒤면 **조합·수정안 하나**. 이 문서에서 **이번 산출물**은 이 목록 중 지금 제시하는 하나를 뜻한다. 한 번에 두 게이트의 산출물을 섞지 않는다. 시안·검증용 코드는 분리된 임시 경로에서 계속 준비할 수 있다.

```
게이트 정지 — 모드 `<mode>`, 미완료: <단계 번호. 단계 이름(빈 항목) | Relevant experience evidence(<Motion|Charts|3D|Graphics>) 동작 시안 | 조합·수정안 재제시>
<사용자 메시지 | 판정 근거>: <착수 승인으로 처리 | 면제로 처리하지 않음 | 정지 이미지뿐이라 미제시로 판정>, 아직 보여드리지 않은 <방향|시안>의 승인으로 처리하지 않았습니다. application source는 수정하지 않습니다.
이번 산출물: <질문 하나 | 시각 방향 세 개 | 고해상도 시안 세 개 | 동작 시안 세 개 | 조합·수정안 하나>
<질문이면> 질문 하나: <결과를 바꾸는 질문> (추천: <AI 추천과 이유>) — 답을 받는 동안 <그다음 게이트의 산출물>을 임시 경로에서 준비합니다.
<산출물이면> <URL·설명·AI 추천안>
```

둘째 줄의 첫 칸은 트리거에 따라 고른다: `ㄱㄱ`·`알아서` 등 착수 발화이면 `<사용자 메시지>: 착수 승인으로 처리`, `시안 없이 바로 구현해` 등 면제 요청이면 `<사용자 메시지>: 면제로 처리하지 않음`, 사용자 메시지 없이 정지 이미지 시안을 재제시하는 경우이면 `<판정 근거>: 정지 이미지뿐이라 미제시로 판정`. 셋 중 하나만 쓴다.

판정: 인터뷰(1·2단계)에 빈 항목이 있으면 질문 하나를 먼저 낸다. 인터뷰가 모두 채워졌고 방향·시안만 미제시이면 질문 없이 그 산출물을 바로 제시한다. 어느 경우에도 `Implementation unlocked: yes`를 먼저 쓰지 않는다.

### 시안의 형식

시안·기술 검증용 코드는 분리된 임시 경로에서 만들고 제품 소스에 반영하지 않는다. 모션·차트·그래픽·3D가 들어가는 동적 시안은 **실제 동작**(재생/초기화, 클릭·필터·스크롤 조작)을 반드시 포함한다. 시작/중간/끝 정지 상태는 동작 시안에 붙이는 보조 자료이며 동작을 대체하지 못한다. 정지 이미지·외부 예제 링크만 있는 시안은 동적 시안으로 인정하지 않는다. 동적 요소를 포함해도 **서로 다른 composition 세 개**라는 기준은 유지한다. 시안의 샘플 데이터·대체 모델은 명시한다.

판정: 시안이 정지 프레임뿐이고 대상에 움직이는 요소(전환·차트 갱신·scroll 연출·3D 조작)가 있으면 그 시안은 미제시 상태다. 게이트 정지 형식으로 이번 산출물을 밝히고(full 4단계면 "고해상도 시안 세 개", scoped 새 표현이면 "동작 시안 세 개") 실제 동작을 포함해 다시 만든다.

모션·차트가 포함된 시안은 클릭·필터·스크롤을 직접 비교할 수 있게 만든다. 신규 디자인의 세 시안 안에 함께 넣어 별도 3×3 선택을 만들지 않는다. 그래픽은 같은 시안에서 시간 흐름·입력 반응·재생/초기화를, 3D 모델은 여러 각도와 재질·조명을 검수한다. 새 모션/차트/그래픽 패턴만 추가하는 scoped 작업은 해당 범위의 동작 비교와 선택만 기록하고 제품 인터뷰·시각 세계관을 다시 시작하지 않는다.

세 시안은 같은 핵심 콘텐츠·대표 데이터를 사용해 구조 차이를 비교할 수 있게 한다. 웹 시안은 실제 stack에서 구현 가능한 반응형 구조와 주요 상태를 보여준다. HTML로 보여줄 때는 로컬 서버의 응답을 확인한 접근 가능한 URL을 제공하고 해당 작업의 서버를 종료 시 정리한다. 이미 승인된 디자인을 작은 변경 때문에 다시 세 시안으로 만들지 않는다.

## 실행 순서

### 모드별 필수 여부

강도는 모든 모드에서 같다. 모드에 따라 달라지는 것은 **범위**와 **write 권한**뿐이다. `refactor`는 보존형(scoped)과 세계관/대표 화면 전면 교체형(full)을 나눠 적는다.

| 단계 | `new` | `rebrand` | `refactor` 보존형 | `refactor` 전면 교체형 | `small-feature` | `audit` |
|---|---|---|---|---|---|---|
| 0. 규칙·범위·잠금 확인 | 필수 | 필수 | 필수 | 필수 | 필수 | 필수; 잠금 유지, 정본·구현노트·gate 파일 생성 금지 |
| 1. 조사 | 필수; 기준선 없음 기록 | 필수; 대표 flow | 필수; 대표 flow | 필수; 대표 flow | 필수; 범위 = 대상 화면 + 인접 패턴 ≤ 2 | 필수; 읽기 전용, 기존 detector만. 보고 후 종료 |
| 2. 요구·경험·방향 확정 | 필수; 게이트 1~4 | 필수; 게이트 1~4 | 필수; 범위 확인 + 새 표현이면 동작 시안 3 | 필수; 게이트 1~4 | 필수; 범위 확인 + 새 표현이면 동작 시안 3 | 대화로 제안만 |
| 3. 도구 선택·준비 | 필수; 앱 의존성은 잠금 해제 후 | 필수; 동일 | 필수; 동일 | 필수; 동일 | 필수; 동일 | 설치 금지 |
| 4. 구현 계획·수용 기준 | 필수 | 필수 | 필수 | 필수 | 필수 | N/A; `Recommended first slice`만 |
| 5. 구현 | 게이트 5 기록 후 | 게이트 5 기록 후 | scoped 게이트 기록 후 | 게이트 5 기록 후 | scoped 게이트 기록 후 | 금지 |
| 6. 검증 | 전체 매트릭스 | 전체 매트릭스 | 전체 매트릭스 | 전체 매트릭스 | 전체 매트릭스; 대상 = 변경 route·state | 기준선 검사만, 설치 없이 |
| 7. 완료·인계 | 필수 | 필수 | 필수 | 필수 | 필수 | 대화 보고 |

### 0. 규칙·범위·잠금 확인

- 실제 Git 루트와 `AGENTS.md`, `CLAUDE.md`, 중첩 규칙, HANDOFF, 기존 제품·디자인 정본을 확인한다. 다중 프로젝트 workspace 루트에 설치하지 않는다.
- 구현에는 설치된 `dev-protocol`을 함께 적용한다. 경로를 현재 환경에서 찾고, plugin 번들에만 있다고 가정하지 않는다. 사용자 승인 범위·worktree·구현노트·배포는 그 스킬을 따른다. Git×Supabase×Vercel이면 해당 프로젝트의 `feature-flow`를 적용한다.
- dirty 파일을 보존한다. 모드·범위·주 목적·유지할 계약을 한 줄로 알린다. `audit`는 구현노트나 정본 파일도 만들지 않고 결과를 대화로 보고한다. 사용자가 별도 보고서 저장을 요청하면 그 문서만 저장한다.
- 구현 작업은 gate template을 사용한다. `small-feature`와 보존형 `refactor`의 신규 전용 게이트는 근거와 함께 `N/A`로 표시한다. 가짜 답변·`complete`/`N/A` 표시로 채우지 않는다.

### 1. 현재 화면과 사용자 과업 조사

[project-audit.md](references/project-audit.md)를 읽는다. stack·버전·토큰·공통 UI·**차트 엔진/표/모션 라이브러리 인벤토리**와 실제 화면을 함께 확인한다. 핵심 과업 하나를 시작부터 완료까지 따라가며 마찰을 찾는다.

조사 **대상**은 모드가 정한다: `small-feature`는 대상 화면과 존재하는 인접 패턴 최대 두 개, `rebrand`/`refactor`는 대표 flow, `new`는 기준선 없음 기록. 대상 안에서는 모든 모드가 같은 항목을 조사한다. 없는 화면이나 문서를 억지로 만들지 않는다.

기존 화면의 정렬·밀도·반응형·상태·console/network 기준선을 남긴다. 새 프로젝트는 기준선 없음으로 기록한다. `audit`는 관찰·검사 결과·추론을 구분해 영향순으로 보고하고 종료한다.

### 2. 요구·경험·디자인 방향 확정

[design-context.md](references/design-context.md)와 선택한 목적의 참조를 읽는다. 발견할 수 없는 제품 결정만 질문한다. 기술 도구 이름보다 원하는 경험을 묻는다: "모델 회전인가, 부품 분해인가, 형태 변형인가", "이 숫자로 어떤 결정을 하는가".

명칭·느낌을 구체화할 필요가 있으면 [intent-to-experience.md](references/intent-to-experience.md)로 **도메인 분석 → 쉬운 경험 이름·통용 명칭·reference·추천 → 보완 요청문**을 기존 인터뷰/방향 선택에 통합한다. 확정된 요구는 재작성·재질문하지 않는다. 그래픽은 연출 인상과 제작/전달 방식을 구분하고, 충분히 명확한 요청도 모드에 필요한 시안 게이트는 유지한다.

기존 `PRODUCT.md`·`DESIGN.md`가 우선이다. 새 정본은 각 승인 시점에 [PRODUCT](assets/PRODUCT.template.md)·[DESIGN](assets/DESIGN.template.md) 템플릿을 채운다. 작은 작업은 기존 정본/구현노트의 해당 부분만 보완한다. 신규 게이트가 필요한 경우 앞의 순서대로 인터뷰·방향·시안을 완료한다.

### 3. 필요한 도구만 선택·준비

[tooling.md](references/tooling.md)를 따른다. 실제 stack과 설치 상태를 확인한 뒤 위 기본 도구 정책에 맞게 재사용·설치·연결한다. 외부 서비스는 필요한 [기능 권한](references/tool-capabilities.md)을 확인한다. 유료 사용자는 이용 가능한 포함 기능을 활용하고, 무료 사용자는 결과물의 다운로드·상업 이용·웹 전달까지 가능한 무료 경로를 사용한다. 구독 여부만으로 모든 기능·API·추가 과금이 허용된다고 간주하지 않는다.

디자인 보조 스킬은 모드와 부족한 역량에 맞게 선택한다. 설치 스크립트는 기본이 plan-only다: `python3 <skill-dir>/scripts/setup_design_tools.py --project <git-root> --mode <mode> --json`으로 계획을 출력해 source·명령·생성 파일을 검토한 뒤, 승인된 범위에서만 같은 명령에 `--apply`를 붙여 실행한다. `--mode audit`는 `--apply`를 거부한다. 스크립트 옵션과 설치 버전은 [tooling.md](references/tooling.md)가 소유한다. 방향/시안 제작에 보조 도구가 필요하면 2단계 중 준비해도 되지만 게이트를 건너뛰지 않는다. 실제 앱 의존성은 구현 잠금 해제 뒤 프로젝트 package manager로 설치한다. `audit`는 설치하지 않는다.

### 4. 구현 계획과 수용 기준

변경/제외 화면, 보존할 기능·데이터·권한·URL·이벤트, 재사용할 컴포넌트, 필요한 UI 상태, 실행할 검증 명령을 정한다. [web-quality.md](references/web-quality.md)를 웹 품질 기준으로, 업무 UI는 [work-ui-surfaces.md](references/work-ui-surfaces.md)를 추가 기준으로 사용한다.

중요한 과업에 대해 **사용자 행동 → 보이는 반응 → 완료 조건**을 짧게 적는다. 예: 기간 필터 변경 → 선택 상태와 조회 상태 표시 → 카드·차트·표에 같은 기간 반영. 이번 목적에 필요한 성능·데이터·3D 기준만 추가한다. 레거시 차트 엔진이 있으면 이번 이관 범위와 전체 이관 제안을 계획에 포함한다. 범위 밖 개선은 후속 항목으로 남긴다.

### 5. 구현·정렬·사용감 다듬기

- `Implementation unlocked: yes`와 모드에 필요한 근거를 확인한다.
- 기존 토큰·공통 컴포넌트·semantic HTML을 우선한다. 프레임워크를 React로 가정하지 않는다.
- 구조와 주요 축 → 정보 위계·타이포 → 간격·밀도 → 상태·반응 → 장식 순으로 다듬는다. 그리드에 맞는 숫자뿐 아니라 글자·아이콘의 시각적 정렬도 확인한다.
- 승인된 방향을 화면에 구현한다. 임의의 카드 중첩·gradient·glow·거대한 제목·bounce를 기본값으로 넣지 않는다. 의도된 브랜드 표현은 근거로 유지한다.
- 입력·hover·focus·active·disabled·loading 상태는 **컴포넌트에 해당하는 것만** 구현한다. 명확한 피드백과 오류 복구를 제공하고 실제 성공 전에 성공 표시를 만들지 않는다.
- 모션과 차트는 선택된 동작·데이터·토큰을 실제 코드에 연결한다. 레거시 차트 엔진은 대상 화면에서 제거하고 같은 데이터 계약을 유지한다. 그래픽·3D는 AI가 제작 원본과 선택한 영상/시퀀스/실시간 자산을 준비하고 실제 브라우저로 옮겨 확인한다. 패키지 설치·외부 사이트 링크·자산 생성만으로 구현 완료를 보고하지 않는다.
- 기능 계약 변경이 필요하면 영향과 기존 승인 범위를 대조해 `dev-protocol`에 기록한다.

### 6. 실제 검증과 한 번의 개선 검토

[verification.md](references/verification.md)를 따른다. build/lint/test, source/URL detector, 브라우저 desktop/mobile, 핵심 과업 직접 조작과 목적별 검증을 실행한다. 검증 매트릭스는 모드와 무관하게 전체를 실행하고, 대상 route·state만 모드의 범위에 맞춘다. 자동 검사는 사용자 평가를 대신하지 않는다.

동일 조건(같은 route·viewport·data·state·theme·auth)의 전후 화면을 비교하고 발견된 범위 내 문제를 수정한다. 수정한 부분과 영향받는 검증만 반복한다. 해결되지 않은 중요한 실패가 있으면 완료로 표시하지 않는다. 미실행 항목·환경 제약·의도된 예외는 명시한다.

불만족 피드백은 [feedback-improvement.md](references/feedback-improvement.md)로 **기대와 실제 차이 → 원인 → 디자인/코드/제작 경로 수정 → 재확인**으로 이어간다. 재현된 공통 지침 결함만 승인된 범위에서 스킬에 반영한다. 프로젝트 취향을 전역 규칙으로 만들거나 모든 불만에 스킬을 자동 수정하지 않는다.

### 7. 완료·인계

사용자 관점으로 **무엇이 쉬워졌는지, 확인할 화면/URL, 실제 검증 결과, 남은 한계**를 보고한다. 사용자 피드백 없이 "만족도 최고"나 임의 점수를 붙이지 않는다. 승인된 미리보기와 실제 결과의 차이를 짧게 설명한다.

디자인 결정은 기존 정본에 남긴다. 레거시 엔진이 남아 있으면 남은 사용처 수(실제 레거시 잔존 사용처·기록된 예외·미처리 이관 대상, 고유 route 기준)와 다음 이관 범위를 정본 또는 후속 항목에 기록한다. commit/push·배포·HANDOFF·worktree 정리·운영 후 knowns는 `dev-protocol`에 위임한다. 로컬 변경이나 preview를 운영배포로 간주하지 않는다.

## 대표 흐름 예시

아래는 스킬 텍스트만 보고 에이전트가 따라야 할 순서다. 파일명은 이 스킬의 `references/` 기준이다.

### S1. React ERP, ECharts 매출 대시보드의 차트 하나를 "예쁘게"

1. 읽는 파일: SKILL.md → [mode-selection.md](references/mode-selection.md)("예쁘게"는 모호) → [experience-routing.md](references/experience-routing.md) → [project-audit.md](references/project-audit.md) → [design-context.md](references/design-context.md) → [data-surfaces.md](references/data-surfaces.md) → [work-ui-surfaces.md](references/work-ui-surfaces.md)(같은 화면의 카드·표·필터바) → [tooling.md](references/tooling.md)(Bklit 설치 경로 확인 표) → [verification.md](references/verification.md).
2. 판정: 기존 브랜드·정본이 있고 차트 하나의 표현 변경이면 `small-feature`(대시보드 위계 전체를 정리하면 보존형 `refactor`). 주 목적은 데이터 대시보드, 보조 업무 UI(필터바·상세 표). 범위 = 해당 차트 + 같은 화면의 다른 레거시 차트(확인된 개별 차트 예외가 없는 화면은 모든 레거시 차트를 함께 이관; 개별 차트 예외가 기록되면 그 차트만 공존 허용, route는 `기록된 예외`) + 같은 화면의 카드·표 + 인접 차트 패턴 ≤ 2.
3. 조사·확인: 인벤토리를 **파일 수와 화면(route) 수로 나눠** 기록한다. 예: `echarts` 사용처 파일 7(공통 wrapper 1) / 화면 5(매출 대시보드에 차트 파일 2개, 나머지 4 화면에 1개씩; 공통 wrapper `EChart.tsx`는 파일 7에 포함). 지표 정의·기간·비교 기준은 코드/API로 확인하고 되묻지 않는다. 발견할 수 없으면 질문 하나: "이 차트로 어떤 결정을 하는가". 사용자에게 한 줄로 알린다: "모드 `small-feature`, 목적 데이터 대시보드. ECharts 사용처 파일 7(공통 wrapper 1) / 화면 5 중 이번 범위는 매출 대시보드 1 화면의 Bklit 이관. 요청한 매출 추세 차트 외에 이 화면의 다른 ECharts 차트 1개(채널별 비교)도 같은 화면 규칙에 따라 이번 범위이며, 승인된 표현이 있으면 재사용하고 새 표현이면 시안에 포함합니다. 나머지 4 화면은 전체 이관 제안".
4. 시안: 공식 Bklit 예제를 브라우저에서 직접 조작하고 URL·행동·채택 표현을 기록(접근 불가의 실제 근거가 있을 때만 실행본 확보·로컬 실행·방향 보류 중 하나를 결정받는다; 관찰 없는 채택은 없다) → 같은 대표 데이터로 동작 시안 세 개(예: 간결한 업무형 / KPI+추세 / 비교·탐색; 표현·정보 위계·탐색 동작 세 축 중 최소 두 축이 다름)를 임시 경로에서 만들어 로컬 서버 URL로 제시 → AI 추천 명시 → 사용자 선택. ECharts 차트를 "스타일만 다듬는" 안은 만들지 않는다.
5. 구현: gate template scoped 기록(1~4 `N/A` + 근거; Charts 행에 시안 선택; Legacy 행에 인벤토리·이번 범위·예외 판정·실행 계획. 실제 이관·parity·제거·전체 이관 결정은 `구현 후 갱신 예정`) → 잠금 해제 → shadcn registry로 필요한 Bklit component만 추가(tooling.md 설치 경로 확인 표 기록) → 대상 화면의 ECharts 차트 2개를 Bklit로 교체하고 이 화면의 ECharts import 제거 → 데이터 계약·필터 연동 유지.
6. 검증: 이전 ECharts 차트와 **동일 데이터 parity**(같은 route·필터·기간·data·theme·viewport·auth에서 수치·tooltip·범례·export·상태·키보드/터치·모바일 대조, 절차는 verification.md), 원본 집계 vs 카드·차트·표 수치 대조(Numerical reconciliation 표, 최소 두 조건), 기간/필터 변경, empty·한 건·오류·느린 요청, 모바일 범례·tooltip clipping, reduced motion, 전후 성능 실측(차트 엔진 교체는 성능 영향이 있는 변경), build/lint/test, source/URL detector, Playwright 전후.
7. 기록: DESIGN `Chart decisions › Legacy chart engine migration`과 gate template의 `구현 후 갱신 예정` 항목을 실제 결과로 갱신한다: 화면 이관률 1/5(고유 route 기준), 파일 기준 잔여 레거시 import 5(화면 컴포넌트 4 + 공통 wrapper 1; 별도 기록), 대상 화면 레거시 import 0건, parity 결과, 잔여 세 값 = 실제 레거시 잔존 사용처 4 화면 / 기록된 예외 0 / 미처리 이관 대상 4 화면(= 5 − 1 − 0). 완료 보고는 "부분 적용: 1/5 화면 이관, 나머지 제안 중" 형식으로 전체 이관 제안(범위·순서·예상 회귀)을 포함해 사용자 결정을 받는다.

### S2. 같은 ERP에 탭 하나 추가

1. 읽는 파일: SKILL.md → [mode-selection.md](references/mode-selection.md)(`small-feature` 범위 가드) → [experience-routing.md](references/experience-routing.md)(업무 UI) → [project-audit.md](references/project-audit.md) → [design-context.md](references/design-context.md) → [work-ui-surfaces.md](references/work-ui-surfaces.md) → [motion-design.md](references/motion-design.md) → [web-quality.md](references/web-quality.md) → [tooling.md](references/tooling.md)(Motion 설치 버전·연결) → [verification.md](references/verification.md).
2. 판정: `small-feature`, 주 목적 업무 UI. 범위 = 탭 목록 + 새 탭 패널 + 인접 탭 패턴 ≤ 2. 전역 토큰·공통 Tabs 컴포넌트의 계약은 변경 금지(변경이 필요하면 영향 범위를 캡처하고 검증).
3. 조사·확인: 인접 탭 패턴에서 typography·spacing·indicator·상태 패턴을 추출한다. 모션 인벤토리로 `motion`/`framer-motion` 설치 버전과 승인된 탭 전환 패턴 유무를 확인한다. 탭 선택의 URL 반영·권한별 노출·초기 탭은 코드로 확인하고, 발견할 수 없는 것만 질문 하나.
4. 시안(세 분기 중 하나, 판정 기준은 `### 공통 원칙`의 **새 표현 판정**): (a) 사용자 결정이 기록된 **승인된** 탭 전환 Motion 패턴이 있으면 재사용하고 "재사용: <패턴 이름>, 기록 위치"를 적는다(시안 없음). (b) 기록 없는 기존 탭 패턴(예: CSS transition 탭)이 있고 새 표현이 아니면(같은 indicator 이동·같은 타이밍 범위를 Motion으로 재구현) 재사용할 수 있다. "기존 코드 패턴 재사용(미승인)"으로 표시하고 원 코드 위치·동작 동일성·새 표현이 아니라는 판정 근거·변경 상태 검증을 연결한다(시안 없음). (c) 기존 패턴이 없거나 새 표현이면(없던 패널 slide·공유 요소 이동·완료 피드백 추가) 공식 Motion 예제 관찰 후 같은 콘텐츠로 동작 시안 세 개(indicator 이동·패널 전환·완료 피드백 차이)를 만들어 사용자 결정을 받는다.
5. 구현: gate template scoped 기록 → 잠금 해제 → 탭 추가, Motion으로 indicator·패널 전환, 방향키/Home/End·focus-visible·ARIA tabs 패턴, 탭 패널의 표·폼은 work-ui-surfaces 기준(열 정렬·숫자 정렬·오류 위치·저장 상태) 적용.
6. 검증: build/lint/test, source/URL detector, Playwright desktop/mobile 전후, 키보드만으로 탭 이동 → 패널 과업 완료, reduced motion, 권한별 상태(비노출/읽기 전용), 공통 컴포넌트를 건드렸으면 다른 화면 회귀 캡처.
7. 기록: 구현노트에 gate evidence와 검증 결과. DESIGN은 (a)면 변경 없음, (b)면 `Motion decisions`에 "기존 코드 패턴 재사용(미승인)"과 판정 근거, (c)면 세 시안 URL·AI 추천·사용자 선택 기록.

### S5. 시안을 보여주기 전에 사용자가 `ㄱㄱ`

상황: `new`, 제품 인터뷰 완료, 디자인 방향 인터뷰 중 접근성 목표만 미확인, 시각 방향·시안 미제시.

```
게이트 정지 — 모드 `new`, 미완료: 2. 디자인 방향 인터뷰(접근성 목표)
`ㄱㄱ`: 착수 승인으로 처리, 아직 보여드리지 않은 시각 방향·시안의 승인으로 처리하지 않았습니다. application source는 수정하지 않습니다.
이번 산출물: 질문 하나
질문 하나: 접근성 목표를 WCAG AA(본문 대비 4.5:1, 키보드만으로 핵심 과업 완료)로 잡아도 될까요? (추천: AA — 업무 화면이고 외부 감사 요건이 없어 AA가 표준입니다) — 답을 받는 동안 시각 방향 세 개를 임시 경로에서 준비합니다.
```

이 질문에 사용자가 `ㄱㄱ`·`추천대로`·`그렇게`라고 답하면 해석표에 따라 **그 질문 하나의 답**으로 AA를 채택하고, 기록 위치 규칙대로 질문은 `Question`, 추천(AA와 이유)은 Design-direction interview 절의 AI recommendation 필드, 사용자 원문 `ㄱㄱ`는 `Real user answer`, 채택한 값 AA는 `Confirmed brand traits, reference/anti-reference, density, platform and accessibility`에 기록한 뒤, 시각 방향 세 개를 URL로 제시한다. 그 답을 시각 방향·시안의 승인으로 확장하지 않는다.

인터뷰가 모두 끝난 상태의 `ㄱㄱ`이면 질문 없이 "착수 승인으로 처리, 시각 방향 세 개를 준비해 URL로 제시"만 밝히고 제시한다. 어느 경우에도 잠금 해제나 source write를 하지 않는다.

## 완료 기준

- 모드·목적·범위와 diff가 일치하고 필요한 실제 사용자 승인 근거(사용자 메시지 원문, 제시 이후 시점)가 gate template에 있다.
- 기존 디자인/기능 계약을 보존하거나 승인된 변경으로 기록했다.
- 정렬·가독성·반응형·관련 UI 상태와 핵심 과업을 실제 화면에서 확인했다.
- 채택한 도구의 역할·근거·비용/호환성 제약과 목적별 검증 결과를 남겼다.
- 레거시 차트 엔진이 있던 경우: 인벤토리 표, 대상 화면의 레거시 import 0건(개별 차트 예외가 기록된 화면은 0건이 아니며 `기록된 예외`로 집계), 동일 데이터 parity 결과, 완료 증거 표와 남은 사용처 수, 전체 이관 제안과 사용자 결정(또는 기록된 비호환 예외)이 있다. `기록된 예외` route와 parity 미실행 route는 `이관 완료`로 표시하지 않는다. 남은 사용처가 있으면 보고는 "부분 적용: N/M 화면 이관, 나머지 제안 중" 형식이다. N·M은 **고유 route(화면) 기준**(M = 인벤토리의 화면/route 행 수, N = `이관 완료` 행 수)이고 파일·import 수는 별도로 기록하며, 잔여는 실제 레거시 잔존 사용처·기록된 예외·미처리 이관 대상(= 전체 대상 − 이관 완료 − 기록된 예외)의 세 값으로 구분한다(정본: [data-surfaces.md](references/data-surfaces.md) `## 레거시 차트 엔진 교체`).
- 업무 UI인 경우: 키보드만으로 핵심 과업 완료, 표·폼·필터의 상태(정렬/필터/페이지, 오류 위치, 저장 상태), 숫자 정렬·단위, 권한별 상태를 [work-ui-surfaces.md](references/work-ui-surfaces.md) 기준으로 확인했다.
- 필요한 의도 보완 또는 생략 근거, 모션·차트·그래픽 동작 선택/기존 승인, 제작 검수·웹 전달과 기능 권한의 근거가 있다. 개인 계정 정보는 공유 정본에 넣지 않는다.
- build/lint/test·detector·브라우저 검증의 실행 결과와 누락이 구분된다. `small-feature`도 같은 매트릭스를 실행했다.
- Claude와 Codex가 같은 정본을 참조하며 정본에 새 결정이 반영됐다.
