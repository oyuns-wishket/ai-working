# 프로젝트 조사

모든 모드에서 같은 항목을 조사한다. 모드는 조사 **대상**(어느 화면·flow)만 정한다. `audit`는 읽기 전용이며 이 문서의 어떤 항목도 설치·write를 허용하지 않는다.

## 읽는 순서

1. 저장소 규칙: `CLAUDE.md`, `AGENTS.md`, 중첩 규칙
2. 현재 작업 이력: impl-notes, HANDOFF, 연결된 issue/spec
3. 제품 맥락: product brief, 요구사항, 사용자 flow
4. 디자인 맥락: `PRODUCT.md`, `DESIGN.md`, design-system 문서, 토큰
5. 구현: app shell, navigation, 공통 UI, 변경 대상 화면
6. 런타임 증거: 대표 URL, 스크린샷, console/network 로그

## 정적 인벤토리

기록한다:

- framework와 버전
- lockfile로 확인한 package manager
- CSS 체계: Tailwind, CSS modules, styled components, vanilla CSS, native
- component library와 icon 체계
- 폰트와 로딩 방식
- theme/color/token 정의
- breakpoint와 layout container
- navigation 모델
- 기존 visual test, Storybook, Playwright
- build, lint, test, dev 명령

`rg`와 프로젝트 manifest를 사용한다. workspace 기본값으로 stack을 추정하지 않는다.

### 차트 엔진·표 라이브러리·모션 라이브러리 인벤토리

차트·표·모션이 범위에 조금이라도 걸리면 모든 모드에서 필수다. `new`는 기준선 화면이 없으므로 대상 화면 이관·parity는 N/A이지만, 같은 저장소에 레거시 엔진이 있으면 인벤토리·판정·전체 이관 제안·공존 기록은 그대로 적용한다. package.json만 보지 않고 실제 import·registry 생성 소스·공통 wrapper까지 센다.

```bash
# 차트 엔진 (레거시 후보 포함): import/require 문의 패키지명을 센다
rg -l -e "(echarts|echarts-for-react|chart\.js|react-chartjs-2|apexcharts|react-apexcharts|highcharts|highcharts-react-official|recharts|@nivo/|victory|plotly)['\"]" --glob '!node_modules' .
# Bklit/shadcn chart source (package 이름이 없을 수 있음)
rg -l -e "bklit" -e "components/ui/chart" -e "ChartContainer" --glob '!node_modules' .
# 표 라이브러리
rg -l -e "(@tanstack/react-table|ag-grid|@mui/x-data-grid|react-data-grid|antd/es/table|@tanstack/react-virtual)['\"]" --glob '!node_modules' .
# 모션 라이브러리
rg -l -e "(motion|motion/react|framer-motion|animejs|gsap|@react-spring|lottie-web|@rive-app)['\"]" --glob '!node_modules' .
# 3D
rg -l -e "(three|@react-three/fiber|@react-three/drei|@google/model-viewer|@splinetool)['\"]" --glob '!node_modules' .
```

명령은 예시이며 stack에 맞게 패턴을 조정한다. 두 번째 검색 결과는 생성 소스와 호출부를 포함하는 **후보 목록**이다. registry 원본·설치 증거(`components.json`, registry 추가 명령 기록, [tooling.md](tooling.md) 설치 경로 확인 표)로 생성 출처를 확인한 파일의 실제 하위 의존성 import(예: 생성된 `components/ui/chart*`가 import하는 `recharts`)만 레거시 후보에서 제외하고 `Retained dependencies` 후보로 분류한다(계수 단위는 [data-surfaces.md](data-surfaces.md) 3. 순서 1). 호출 화면·프로젝트 wrapper의 레거시 import는 검색 결과가 겹쳐도 제외하지 않는다. 판정: 파일이 두 검색에 모두 잡혔는데 생성 출처를 확인할 수 없으면 레거시 후보로 둔다. **구 Recharts wrapper**는 registry 생성 소스가 아닌, Bklit 도입 이전에 프로젝트가 직접 작성한 recharts 기반 chart 컴포넌트/wrapper를 뜻하며 교체 대상이다. 결과를 표로 남긴다. **사용처 파일 수**는 공통 wrapper를 포함해 해당 패키지·wrapper를 import하는 앱 코드 파일 수이고 괄호에 그중 공통 wrapper 수를 적는다(예: `7(공통 wrapper 1)`). **화면(route) 수**는 그 파일들이 렌더되는 고유 route 수다. 화면 이관률 N/M의 M은 화면(route) 수이며 파일 수가 아니다.

| 영역 | 라이브러리 | 버전(lockfile) | 사용처 파일 수 | 화면(route) 수 | 공통 wrapper | 이번 범위 내 사용처 | 판정 |
|---|---|---|---|---|---|---|---|
| 차트 | echarts | 5.x | 7(공통 wrapper 1) | 5 | `components/charts/EChart.tsx` | 1 화면(매출 대시보드: 매출 추세 + 채널별 비교, 차트 2개) | 레거시 → Bklit 이관 대상; 미처리 이관 대상 4 화면 전체 이관 제안 |
| 차트 | Bklit(shadcn registry) | — | 0 | 0 | 없음 | — | 신규 추가 |
| 표 | @tanstack/react-table | 8.x | 12 | 9 | `components/table/DataTable.tsx` | 2 | 재사용 |
| 모션 | framer-motion | 10.x | 9 | 7 | `components/motion/*` | 1 | 호환 버전 재사용, 중복 설치 금지 |

판정 규칙:
- 차트 열에 Bklit 외 엔진이 있으면 **레거시**로 표시하고 SKILL.md의 레거시 교체 정책과 [data-surfaces.md](data-surfaces.md) `## 레거시 차트 엔진 교체`를 적용한다. 예외(비React 등 비호환 판정)는 근거를 같은 표의 판정 열에 쓴다. 이번 작업이 차트를 하나라도 변경할 때만 같은 화면의 레거시 차트 전부를 이번 이관 범위로 묶는다. 탭·폼만 변경하면 같은 화면의 레거시 차트는 인접 대상으로 조사하고 전체 이관을 제안하되 이번 diff에서 변경하지 않는다([mode-selection.md](mode-selection.md) Small feature 판정과 동일). 이관 대상 화면은 표의 "이번 범위 내 사용처"에 화면 수와 차트 수를 함께 적는다. 이관 대상으로 판정된 화면에서, 확인된 개별 차트 예외가 없는 화면은 모든 레거시 차트를 함께 이관한다. 개별 차트의 비호환 예외(필수 기능 부재·실측 성능)가 기록된 화면은 해당 차트에 한해 공존을 허용하고, 예외 범위·의존 비용·재검토 조건을 판정 열에 기록한다. 해당 route는 `기록된 예외`로 집계하며 `이관 완료`나 레거시 import 0건으로 표시하지 않는다.
- 모션 열에 `framer-motion`과 `motion`이 함께 있으면 중복 설치를 기록하고 하나로 정리할 범위를 제안한다.
- 같은 속성(scroll progress·camera·transform)을 두 라이브러리가 제어하는 곳이 보이면 소유권 충돌로 기록한다.
- 이 표는 `audit`에서도 작성한다(읽기 전용 조사 결과이므로 대화로 보고).

## 시각 인벤토리

최소한 캡처한다:

- 전역 shell/header/sidebar
- 밀도가 높은 화면 하나
- 폼 또는 상세 화면 하나
- 정확한 대상 화면
- desktop viewport
- 반응형이 범위에 있으면 mobile viewport

조사 **대상**은 모드가 정한다. `small-feature`는 대상 화면과 존재하는 인접 패턴을 최대 두 개까지 조사한다(두 개 이상이면 두 개, 하나면 하나를 조사하며 부족한 수와 이유를 기록한다). `rebrand`/`refactor`는 모든 route가 아니라 대표 flow, `new`는 기존 UI 기준선 없음을 기록한다. 없는 화면을 만들어내지 않는다. 대상 안에서는 모드와 무관하게 아래 항목을 전부 본다.

관련 사용자 과업 하나를 처음부터 끝까지 따라간다. 사용자가 추측해야 하는 곳, 피드백 없이 기다리는 곳, 입력을 반복하는 곳, 오류에서 복구하는 곳을 적는다. 주 목적은 [experience-routing.md](experience-routing.md)로 고르고 전문 조사는 그 목적에 한정한다.

### 업무 UI 조사 항목

주 목적이 업무 UI이거나 대상에 표·폼·필터가 있으면 [work-ui-surfaces.md](work-ui-surfaces.md)의 기준으로 다음을 관찰해 기준선으로 남긴다.

| 항목 | 관찰할 것 |
|---|---|
| 표 | 열 정렬(텍스트 좌/숫자 우), 고정 헤더·고정 열, 행 높이·밀도, 인라인 편집 유무와 저장 방식, 정렬/필터/페이지 상태의 URL 반영, 선택 행 유지, 빈 결과·오류 표시 |
| 폼 | 라벨 위치·그룹, 필수 표시, 오류 위치와 복구, 저장 상태(제출 중·성공·실패), 입력값 보존, 자동 저장 여부 |
| 필터바 | 적용/초기화 동작, 즉시 적용 vs 명시 적용, 저장된 조건, 결과 수 표시, 카드·차트·표의 필터 일치 |
| 키보드 흐름 | Tab 순서, 표 내 이동, 단축키, Enter/Escape 동작, focus-visible, 모달 focus 복귀 |
| 밀도 | 한 화면에 보이는 행·필드 수, 밀도 조절 기능 유무 |
| 숫자 | 자릿수 정렬, 단위·정밀도 일관성, tabular numerals, 음수·0·누락 표시 |
| 권한별 상태 | 권한에 따른 열·버튼·필드의 숨김/비활성/읽기 전용 표현, 거부 시 안내 |

## 런타임 증거

- 브라우저 console 오류·경고
- 실패한 network 요청
- 가로 overflow
- 잘리거나 접힌 콘텐츠
- 키보드 순서와 focus 가시성
- loading, empty, error, disabled, success 상태
- layout shift와 reduced-motion 동작
- 차트가 있으면: 대표 데이터의 값과 원본 집계 일치 여부, 기간/필터 변경 반응

기존 런타임 버그와 디자인 회귀를 혼동하지 않는다. 편집 전에 기준선 문제를 기록한다.

## 감사 출력

읽기 전용 `audit`에서는 결과를 대화로 보고한다. **사용자가 보고서 저장을 요청한 경우에만** [design-audit.template.md](../assets/design-audit.template.md) 형식으로 그 문서 하나를 저장한다. 에이전트 재량으로 파일을 만들지 않는다. 이미 있는 detector만 사용하고 도구 설치나 프로젝트 설정 생성을 하지 않는다. 검사 도구 부재는 커버리지 한계이지 프로젝트를 변경할 허가가 아니다. 구현 모드에서 감사 결과를 남길 때는 같은 템플릿 필드를 구현노트에 쓴다.

모든 항목을 분류한다:

- `observed`: 소스나 브라우저에서 직접 확인
- `detector`: Impeccable 등 자동 검사 결과
- `inferred`: 확인이 필요한 추정 결과

사용자 영향순으로 우선순위를 매긴다:

- P0: 과업 불가, 콘텐츠 읽기 불가, 보안/데이터 위험
- P1: 핵심 flow가 실질적으로 막힘
- P2: 위계 불일치, 반응형 또는 접근성 결함
- P3: 다듬기와 선택적 개선

각 finding에 증거, 영향 범위, 권장 수정, 회귀 위험을 포함한다. 레거시 차트 엔진이 발견되면 `audit`는 인벤토리·판정·전체 이관 제안까지 대화로 보고하고, 이관·설치·제거·기록 파일 생성은 하지 않는다(data-surfaces·tooling·audit template과 같은 범위).
