# 모드 선택

모드의 정의·보존 범위·게이트 세트의 정본은 [SKILL.md](../SKILL.md)의 `## 작업 분류`와 `## 신규·리브랜딩 절대 게이트`다. 이 문서는 모호한 요청의 판정과 모드별 **범위 가드**를 다룬다. 모드는 범위와 write 권한만 정하고 조사·시안·검증의 강도를 정하지 않는다("범위는 좁게, 강도는 전부").

## 판정 표

| 사용자 요청·프로젝트 상태 | 모드 | 기본 범위 | 하지 않는 것 |
|---|---|---|---|
| 새 제품, 신규 랜딩, 또는 재사용할 디자인 정체성이 없는 경우. 문서 부재만으로 `new`로 전환하지 않는다. 기존 브랜드·토큰·컴포넌트를 디자인 근거로 확인할 수 있으면 변경 의도에 따라 보존형 `refactor` 또는 `small-feature` | `new` | 제품 맥락, 디자인 언어, 토큰, 첫 대표 화면 | 모든 페이지 동시 제작 |
| 로고·색·서체·톤을 새 브랜드로 교체 | `rebrand` | 브랜드 정본과 단계별 화면 전환 | 기능·데이터 모델 재작성 |
| 낡거나 제네릭한 UI를 개선 | `refactor` | 정보 위계, layout, component, responsive | 승인 없는 브랜드 전환 |
| 메뉴·탭·모달·폼·차트 하나·한 화면 추가 | `small-feature` | 인접 UI 패턴을 복제한 최소 diff | 전역 palette·typography 변경 |
| 문제와 개선안만 요청 | `audit` | 읽기, 캡처, finding과 우선순위 | 파일 수정, 설치, issue/commit, 정본 생성 |
| 발표덱·제안서·리포트 신규 제작, 또는 기존 덱 정본(마스터 슬라이드·`DECK.md`) 없음 | `new` | 덱 목적·청중·핵심 메시지, 시각 언어, 대표 슬라이드 | 전 슬라이드 동시 제작 |
| 기존 덱·리포트의 위계·레이아웃 개선 | `refactor` | slide grid, typography scale, 도표 표현 | 승인 없는 브랜드 전환 |
| 기존 덱에 슬라이드·섹션 추가 | `small-feature` | 기존 마스터 슬라이드를 복제한 최소 diff | 전체 palette·템플릿 변경 |

`refactor`는 두 게이트 세트 중 하나를 쓴다. 기존 정체성·대표 화면의 composition을 보존하면 **보존형**(scoped 게이트), 새 시각 세계관을 도입하거나 대표 화면의 composition을 전면 교체하면 **전면 교체형**(`new`와 같은 5단계 full 게이트). 판정 기준은 아래 `### Refactor`에 있다.

## 모호 사례

각 사례는 **모드 → 범위 → 읽을 참조** 순으로 적는다.

- "대시보드 예쁘게": 기존 브랜드·토큰·컴포넌트를 디자인 근거로 확인할 수 있으면(`DESIGN.md`가 없어도) 보존형 `refactor`, 차트 하나만이면 `small-feature`. 재사용할 디자인 정체성이 없는 새 제품이면 `new`. 범위 = 요청한 화면과 그 화면의 카드·차트·표. 읽을 참조: [experience-routing.md](experience-routing.md)(데이터 대시보드), [project-audit.md](project-audit.md)(차트 엔진 인벤토리), [data-surfaces.md](data-surfaces.md), [work-ui-surfaces.md](work-ui-surfaces.md)(같은 화면의 표·필터바), [verification.md](verification.md). 레거시 차트 엔진이 있으면 그 화면의 차트는 Bklit로 이관하고 전체 이관을 제안한다(정본: data-surfaces.md `## 레거시 차트 엔진 교체`). 확인된 개별 차트 예외가 없는 화면은 모든 레거시 차트를 함께 이관한다.
- "기존 ECharts 대시보드를 Bklit로 다 바꿔줘": 시각 세계관·대표 화면 composition을 유지하고 **차트 체계만 이관**하면 보존형 `refactor` + 차트 체계 이관. 범위 = 인벤토리에 잡힌 모든 차트 사용처; 공통 wrapper·토큰과 종류별 예외를 나눠 승인 범위에서 순서대로 이관한다. 대표 화면의 composition 자체를 새로 짜면 전면 교체형 → full 게이트. 어느 쪽이든 새 차트 표현은 같은 데이터로 동작 시안 세 개를 거친다. 읽을 참조: [project-audit.md](project-audit.md)(차트 엔진 인벤토리), [data-surfaces.md](data-surfaces.md), [verification.md](verification.md). "다 바꿔줘"는 이관 승인이지 시안 승인이 아니다.
- "ERP 표 가독성 개선": 표 하나·한 화면이면 `small-feature`, 여러 화면의 표 체계(열 정렬·밀도·고정 헤더·숫자 정렬 규칙)를 통일하면 보존형 `refactor`. 범위 = 대상 표 + 인접 표 패턴 ≤ 2(또는 대표 표 flow). 브랜드·전역 토큰은 변경 금지. 읽을 참조: [work-ui-surfaces.md](work-ui-surfaces.md), [web-quality.md](web-quality.md), [project-audit.md](project-audit.md)(표 라이브러리 인벤토리).
- "폼 정리": 폼 하나면 `small-feature`, 폼 패턴(라벨·그룹·오류 위치·저장 상태)을 앱 전체에서 통일하면 보존형 `refactor`. 범위 = 대상 폼 + 인접 폼 패턴 ≤ 2. 입력값 보존·검증 규칙·제출 계약은 보존 대상. 읽을 참조: [work-ui-surfaces.md](work-ui-surfaces.md), [web-quality.md](web-quality.md), [motion-design.md](motion-design.md)(저장/오류 피드백 전환).
- "필터 UX": 필터바 하나면 `small-feature`, 목록 화면 전반의 필터 모델(적용/초기화·URL 반영·저장된 조건)을 바꾸면 보존형 `refactor`. 범위 = 필터바 + 그 결과가 반영되는 표/카드/차트. URL·뒤로가기·검색어 유지 계약은 보존. 읽을 참조: [work-ui-surfaces.md](work-ui-surfaces.md), [data-surfaces.md](data-surfaces.md)(필터와 집계 일치), [motion-design.md](motion-design.md).
- "메뉴 추가하면서 전반적으로 정리": 먼저 `small-feature`; 전반 정리는 별도 `refactor` 제안. 한 작업에 두 모드를 섞지 않는다.
- "브랜드 컬러만 바꿔": token 영향 범위를 확인한다. 전체 인상을 바꾸려는 목적이면 `rebrand`, 지정 토큰 치환이면 좁은 보존형 `refactor`.
- "레퍼런스처럼 만들어": 기능·콘텐츠 구조가 같지 않으면 시각 요소만 분해해 채택한다. 복제 요청으로 해석하지 않는다. 읽을 참조: [design-context.md](design-context.md)의 `## 레퍼런스`.
- "모바일 화면도": 별도 제품이 아니라 기존 범위의 responsive acceptance criterion으로 포함한다.
- "ERP에 상품 탐색·장바구니·예약 화면 추가": 화면 수보다 디자인 정체성 보존 여부로 판단한다. 기존 정본을 따르는 기능 확장은 `small-feature`의 scoped 게이트를 적용하고, 별도 소비자 서비스의 시각 언어를 새로 정하면 그 범위에 `new`의 full 게이트를 적용한다. 어느 쪽이든 신규 모션·차트 표현의 비교는 소유 참조의 규칙을 따른다.
- "발표덱 만들어줘": 산출물 자체가 시각물이므로 이 스킬의 대상이다. 기존 **덱 정본(마스터 슬라이드·`DECK.md` 또는 동등 문서)**이 있으면 `small-feature` 또는 `refactor`, 없으면 브랜드 가이드가 있어도 `new`이며 `new`의 절대 게이트를 그대로 통과한다. 이때 브랜드 토큰은 디자인 방향 인터뷰의 입력으로 재사용한다(브랜드 가이드만으로는 `small-feature`의 기본 범위인 "기존 마스터 슬라이드 복제"가 성립하지 않는다). 읽을 참조: [standalone-visuals.md](standalone-visuals.md)(같은 판정).
- "간단히 슬라이드 몇 장만": "간단히"는 게이트 면제가 아니다. 기존 덱 정본(마스터 슬라이드·`DECK.md`)이 있으면 범위를 `small-feature`로 좁히고 그 정본을 따른다. 덱 정본이 없으면 브랜드 가이드가 있어도 `new`다.
- "리포트/대시보드 뽑아줘": 데이터 산출이 목적이면 이 스킬 밖이다. **보여주는 형태**를 새로 정해야 하면 시각 산출물로 보고 모드를 고른다.
- "우리 관리자 화면 뭐가 문제인지만 봐줘": `audit`. 읽기 전용, 설치·write·issue 금지. observed/detector/inferred로 분류해 대화로 보고한다. 읽을 참조: [project-audit.md](project-audit.md), 업무 UI 항목은 [work-ui-surfaces.md](work-ui-surfaces.md).

판정: 요청에 "만", "간단히", "하나만"이 있으면 **범위**를 좁히는 근거로만 쓴다. 조사 항목·동작 시안(새 표현일 때)·검증 매트릭스를 줄이는 근거로 쓰지 않는다.

## 범위 가드

### New

- 첫 대표 화면과 공통 토큰으로 방향을 검증한 뒤 확장한다.
- `PRODUCT.md`와 `DESIGN.md` 없이 구현부터 시작하지 않는다.

### Rebrand

- 브랜드 자산, legal name, 로고 사용 규칙을 사용자 제공 또는 공식 자료로 확인한다.
- old/new token mapping과 rollout 순서를 남긴다.
- 모든 화면을 한 번에 바꾸기보다 shell 또는 대표 flow에서 승인받는다.

### Refactor

- 사용자 flow, route, API, analytics event, permission을 acceptance criterion에 보존 대상으로 적는다.
- DOM 구조 변경이 테스트나 접근성에 미치는 영향을 확인한다.
- DOM 변경량만으로 새 시각 세계관이라고 판단하지 않는다. 기존 chart의 숫자/범례 정리, 브랜드를 유지한 모션 축소, 레거시 차트 엔진의 Bklit 이관(같은 정보 위계 유지)은 **보존형**이다. 대표 화면의 composition 자체를 전면 교체하거나 palette·typography·layout 원리를 새로 정하면 **전면 교체형**으로 SKILL.md의 full 게이트를 따른다.
- 보존형이라도 새 차트·모션 표현이 들어가는 구간은 같은 데이터/콘텐츠로 동작 시안 세 개를 비교한다.

### Small feature

- 범위만 좁다. 조사 항목, 공식 예제 관찰, 새 표현일 때의 동작 시안 세 개, 검증 매트릭스는 `new`와 동일하다.
- 조사 **대상**은 대상 화면과 존재하는 인접 패턴을 최대 두 개까지다. 두 개 이상이면 두 개, 하나면 하나를 조사하며 부족한 수와 이유를 기록한다. 그 안에서 typography, spacing, color, radius, state pattern, 차트/표/모션 라이브러리 사용을 전부 추출한다. 작은 수정을 위해 없는 화면을 만들지 않는다.
- 새 token은 기존 token으로 표현할 수 없을 때만 추가한다. 브랜드·전역 palette·typography는 변경하지 않는다.
- 공통 component 변경은 해당 메뉴 밖 영향 범위를 캡처하고 검증한다.
- 인접 패턴이 기본 도구(Motion/Bklit)가 아닌 레거시 구현(예: CSS transition만 있는 탭, ECharts 차트)이면 **새 화면·새 요소는 기본 도구로 구현**하고, 인접 레거시는 인벤토리와 이관 제안으로 남긴다(절차는 [data-surfaces.md](data-surfaces.md) `## 레거시 차트 엔진 교체`와 동일). 레거시 패턴을 복제해 새 요소를 만들지 않는다. 같은 속성에 두 엔진을 붙이지 않는다.
- 대상에 레거시 차트 엔진이 있으면 그 차트를 Bklit로 이관하고 전체 이관을 제안한다. "작은 작업이니 기존 엔진 유지"는 허용된 예외가 아니다(예외 판정은 data-surfaces.md `## 레거시 차트 엔진 교체`). 판정: 이번 작업이 차트를 하나라도 변경하면 그 화면의 레거시 차트 전부가 **대상**이다(확인된 개별 차트 예외가 없는 화면은 모든 레거시 차트를 함께 이관). 이번 작업이 차트를 변경하지 않으면(예: 탭·폼 추가) 같은 화면의 레거시 차트는 **인접**이며 위 항목대로 인벤토리·전체 이관 제안으로 남기고 이번 diff에서 바꾸지 않는다.
- 검증 **대상**은 변경된 route·state와 공통 컴포넌트 영향 범위다. 매트릭스 항목(build/lint/test, detector, Playwright desktop/mobile, 키보드, reduced motion, 상태)은 생략하지 않는다.

### Audit

- 심각도보다 사용자 영향과 수정 비용을 함께 표시한다.
- 자동 finding(detector), 직접 관찰(observed), 추론(inferred)을 구분한다.
- source write·설치·issue/commit·정본 생성을 하지 않는다. 검사 도구가 없으면 공백으로 보고한다.

### 앱이 아닌 시각 산출물(덱·제안서·리포트)

- 모드와 게이트는 앱 작업과 동일하다. Git 프로젝트가 아니라는 이유로 인터뷰·3방향·3시안을 줄이지 않는다.
- comp는 전체 덱이 아니라 대표 슬라이드(표지 + 핵심 본문) 기준으로 만들고, 승인 뒤 나머지를 전개한다.
- 정본은 산출물 디렉토리의 `DECK.md`(또는 동등 문서)에 남긴다: 목적, 청중, 핵심 메시지, palette, typography, slide grid, 채택·비채택 레퍼런스.
- 검증은 lint·build 대신 실제 렌더 확인으로 치환한다: 브라우저 전 슬라이드 확인, 투사 비율, overflow·폰트 fallback·이미지 누락, 대비. 상세는 [standalone-visuals.md](standalone-visuals.md).
