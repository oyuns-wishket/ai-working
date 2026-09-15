# 제품·디자인 맥락

`PRODUCT.md`·`DESIGN.md`에 무엇을 어떤 근거로 적는지의 소유 파일이다. 필드는 [PRODUCT.template.md](../assets/PRODUCT.template.md)·[DESIGN.template.md](../assets/DESIGN.template.md)를 따르며, 이 문서의 기록 항목과 템플릿 절·필드는 1:1로 대응한다. 템플릿에 없는 필수 기록이나 본문에 없는 템플릿 필드가 생기면 둘 중 하나를 고친다(템플릿 필드 변경은 assets 소유, 기록 기준 변경은 이 문서 소유).

## 출처 우선순위

1. 사용자가 확인한 브랜드/제품 요구
2. 기존 프로젝트의 `PRODUCT.md`, `DESIGN.md`, design-system 문서
3. 기존 운영 UI와 재사용 가능한 컴포넌트
4. 레퍼런스 디자인(채택/비채택 요소로 분해)
5. Taste Skill 또는 모델이 생성한 제안

일반 스킬이 확립된 프로젝트 체계를 조용히 덮어쓰지 않는다.

## 최소 제품 질문

발견할 수 없는 값만 묻는다:

- 사용자는 어떤 일을 완료하는가?
- 주 사용자는 누구이고 숙련도는 어느 정도인가?
- 브랜드/마케팅 표면인가, 제품/업무 표면인가?
- 이 페이지에서 사람이 이해하거나 끝내야 하는 것은 무엇인가? [experience-routing.md](experience-routing.md)의 여섯 목적 중 무엇에 해당하는가?
- 어떤 현재 동작·정체성을 유지해야 하는가?
- 어떤 결과가 나오면 이 변경이 실패인가?

`new`·`rebrand`는 브랜드 성격, reference/anti-reference, 콘텐츠 밀도, 우선 platform, 접근성 목표도 확정한다. 답이 구현을 바꾸는 결정은 한 번에 하나씩 묻는다. 예외는 아래의 요약 확인 라운드 하나뿐이다.

`PRODUCT.md`가 없는 새 제품은 저장소 증거로 그럴듯한 답을 추정할 수 있어도 실제 사용자 답변 또는 **항목별 값·추정 근거를 열거한 요약 확인 라운드**를 최소 한 번 받는다. 요약 확인 라운드는 추정한 항목마다 "항목 = 값 (근거: 파일·화면)"을 열거한 하나의 질문이며, 그 뒤의 `네`·`맞아`·`ㄱㄱ`는 열거된 항목 전부의 확인이고 열거되지 않은 항목의 답이 아니다(처리·기록 위치는 [SKILL.md](../SKILL.md) `### 사용자 메시지 해석표`). 값·근거를 열거하지 않은 요약은 확인 라운드가 아니며 질문 하나로 처리한다. "생각한 디자인 없음"은 시각 권한이 열려 있다는 뜻이며, 제품 진실이나 시각 방향 승인을 모델에게 위임한 것이 아니다.

`new`·`rebrand`의 구현 전 순서는 [SKILL.md](../SKILL.md) `## 신규·리브랜딩 절대 게이트`의 5단계(제품 인터뷰 → 디자인 방향 인터뷰 → 시각 방향 세 개 → 고해상도 시안 정확히 세 개 → 구현 잠금 해제)를 따른다. 승인의 정의, `ㄱㄱ`·위임·부분 승인의 처리, subagent/reviewer의 권한도 SKILL.md가 소유한다. 여기서는 반복하지 않는다.

## PRODUCT.md 기록 항목

| 템플릿 절 | 필드 | 기록 기준 |
|---|---|---|
| 헤더 | Status, Last verified, Sources | 실제 사용자 답변 또는 항목별 값·추정 근거를 열거한 요약 확인 라운드의 확인 이후에만 `approved`. `audit`는 생성하지 않는다 |
| Product | Name, One-line purpose, Surface(brand/marketing / product/work / mixed), Primary user, User expertise, Differentiation | 제품 인터뷰 답변 또는 기존 문서. 추정이면 표시. Differentiation은 제품 인터뷰의 "차별점" 답변이며 gate template `Product interview`의 확인 항목(differentiation)과 같은 값 |
| Core jobs | 1–3 | 사용자가 완료하는 일 순서대로. 화면 목록이 아니라 과업 |
| Success criteria | User can, Business outcome, Experience outcome, Failure criteria, Representative task(user action → visible response → completion condition), Primary website purpose, Mixed-purpose routes/sections and secondary purposes | Failure criteria는 제품 인터뷰의 "어떤 결과가 나오면 실패인가" 답변이며 gate template `Product interview`의 확인 항목(failure criteria)과 같은 값. Primary website purpose는 [experience-routing.md](experience-routing.md)의 여섯 목적(업무 UI, 커머스, B2C, 데이터 대시보드, 홍보·콘텐츠, 그래픽·3D 체험) 중 하나. 혼합이면 Mixed-purpose 필드에 구간별 목적을 적는다 |
| Constraints | Must preserve, Must not do, Accessibility target, Supported platforms | 보존 계약(route·API·권한·데이터)과 접근성 목표(예: WCAG AA) |
| Current scope | Included, Excluded, Follow-up | 이번 범위와 후속 항목. 레거시 엔진 전체 이관 제안·유예 결정은 Follow-up에 남긴다 |

## DESIGN.md 기록 항목

결정은 구체적으로 적는다: palette 스크린샷이 아니라 이름 있는 토큰과 용도, "부드럽게"가 아니라 선택한 timing/easing. 미확인·미실행을 `N/A`로 감추지 않는다(`N/A`는 대상 자체가 없을 때만).

| 템플릿 절 | 필드 | 기록 기준 · 근거 소유 파일 |
|---|---|---|
| 헤더 | Status, Last verified, Product context, Existing design-system source | 기존 design-system 문서가 있으면 경로를 적고 아래 `## 기존 design-system 이관`을 따른다 |
| Direction | Design intent, Brand traits, Product density, Dominant visual anchor, References adopted/rejected + Reference/Adopt/Reject/Reason 표 | 디자인 방향 인터뷰와 선택된 시각 방향. 레퍼런스는 아래 `## 레퍼런스` 규칙 |
| Web experience decisions | Primary purpose and affected routes/sections; Intent analysis; When proposed; Core user task and visible completion condition; Existing components/tools reused; Additional tools and the task/default policy or compatibility reason; Official documentation/version/license checked; Official example URL and observation date, action → observed result, adopted features(→ Official example comparison 링크); Reference/approved preview → implementation comparison: present / adapted / absent, evidence and reason(→ Official example comparison·Verification evidence 링크); Alignment axes and information density; Mobile transformation and keyboard behavior; Loading, failure recovery, and reduced-motion behavior; Performance measurement conditions and target; For data; For graphics/3D | 목적은 [experience-routing.md](experience-routing.md), 의도 보완은 [intent-to-experience.md](intent-to-experience.md), 도구 기본값/비호환 이유는 SKILL.md 도구 선언, 품질 기준은 [web-quality.md](web-quality.md). 공식 예제 관찰·대조 두 필드는 아래 `Official example comparison` 표를 링크하고 값을 복사하지 않는다 |
| Motion decisions (web UI) | Page/section task; Brand tone and recommended motion intent; Official observation/adoption/result(→ Official example comparison 표); Three same-content interactive comparison URLs, AI recommendation and actual user choice, or existing approved preset, or 기존 코드 패턴 재사용(미승인): 원 코드·동작 동일성·새 표현 아님 판정 근거·변경 상태 검증; Component/state coverage and selected timing/easing/distance/spring; Anime.js/Motion property ownership and installed/reused source; If GSAP exception; Continuous input/reselection/reset and hover/pin priority, keyboard/touch; Reduced motion on initial load and live setting changes; Cleanup on unmount/route re-entry, measured performance | [motion-design.md](motion-design.md). 시안 필드는 세 분기 중 하나다: 새 표현이면 동작 시안 세 개의 URL·AI 추천·사용자 선택; 승인 패턴 재사용이면 승인된 preset 이름과 기록 위치; 기록 없는 기존 코드 패턴을 새 표현 없이 재사용하면 "기존 코드 패턴 재사용(미승인)"과 원 코드·동작 동일성·새 표현 아님 판정 근거·변경 상태 검증(새 표현 판정은 SKILL.md `### 공통 원칙`). GSAP 예외는 SKILL.md 도구 선언의 문장 조건(Anime.js onScroll/Motion useScroll로 구현 불가를 공식 문서·실측으로 확인)을 충족한 경우만 |
| Work UI decisions | Task and routes; Table columns; Bulk actions; Table structure and density; Sort/filter/pagination; Forms; Inline editing; Filter bar; Keyboard and pointer; Numbers; Permission and state; Responsive and zoom; Verification | [work-ui-surfaces.md](work-ui-surfaces.md). 업무 표·폼·필터·입력 흐름을 변경하거나 영향받으면 필수. 없는 요소만 개별 N/A |
| Chart decisions (when charts change) | Bklit component/source reused or added, compatibility exception and alternative/user decision; Installation evidence; Three same-data interactive comparisons, AI recommendation and actual user choice, or approved chart pattern, or 기존 코드 패턴 재사용(미승인): 원 코드·동작 동일성·새 표현 아님 판정 근거·변경 상태 검증; Official observation/adoption/result; Metric definition/source, unit/precision/timezone/period/comparison/aggregation/update time, 0/null/missing rules; Chart type and task, filters/drill-down/tooltip/legend/export, accessible summary/table and data checks; Approved surface/palette/typography/hierarchy/axis/fill/marker/selection/state contract; Selection/hover/pin/reset and chart-summary-table correspondence, period update/geometry continuity; Mobile/long legend/first-last point clipping, live reduced motion, representative data/performance evidence | [data-surfaces.md](data-surfaces.md). 시안 필드는 Motion과 같은 세 분기(새 표현 시안 세 개 / 승인 패턴 재사용 / 기존 코드 패턴 재사용(미승인) + 원 코드·동작 동일성·판정 근거·변경 상태 검증). 비호환 예외는 네 기준(비React / 명시적 다른 엔진 계약 / 필수 기능 부재 / 대표 데이터 실측 성능 문제) 중 어느 것인지와 근거. 호환 정의(React + shadcn `components.json`·Tailwind 기반 chart source를 기존 CSS 체계와 충돌 없이 추가 가능)와 도입 결정 하나는 data-surfaces.md 2. 판정. 설치 증거는 [tooling.md](tooling.md) |
| Chart decisions › Legacy chart engine migration | Legacy inventory; Target migration; Full migration proposal; Actual user decision; Remaining coexistence; Removal evidence; Retained dependencies; Post-removal checks; Completion claim + 인벤토리 표(화면/route 행) + 완료 증거 표(대상 화면 레거시 import 건수는 파일 수) + Remaining usage count 표(화면 이관률 N/M(고유 route) · 사용처 파일 수/공통 wrapper 수 · 실제 레거시 잔존 사용처 · 기록된 예외 · 미처리 이관 대상 · 다음 이관 범위) + Next migration scope + parity 표 | [data-surfaces.md](data-surfaces.md) `## 레거시 차트 엔진 교체`의 인벤토리·판정·순서·공존 규칙·완료 증거 표를 그대로 사용. parity 절차는 [verification.md](verification.md). 레거시와 호환성 예외가 모두 없을 때만 조사 근거와 함께 절 전체를 N/A로 표시한다. 레거시 없이 호환성 예외만 있으면 Target migration에 예외 판정·대안·실제 결정 근거를 기록하고 이관/parity/제거 항목만 N/A로 둔다. 과도기 보고는 "부분 적용: N/M 화면 이관, 나머지 제안 중" 형식이며 N·M은 고유 route 기준(파일·import 수는 별도), 잔여는 실제 레거시 잔존 사용처·기록된 예외·미처리 이관 대상 세 값. 잠금 해제 전에는 Legacy inventory·Target migration의 범위·예외 판정·실행 계획만 채우고 parity·Removal evidence·Actual user decision(전체 이관)은 `구현 후 갱신 예정`으로 표시한다(SKILL.md `## 신규·리브랜딩 절대 게이트`) |
| Numerical reconciliation | 필터/기간 × 원본 집계 / 카드 값 / 차트 값 / 표 합계 / 일치 여부 표 | [data-surfaces.md](data-surfaces.md) 직접 검증. 데이터 화면이면 최소 두 조건(기본 + 변경한 필터/기간). 차트가 없으면 그 열만 N/A |
| Assisted graphics/3D and external capabilities | 템플릿의 17개 필드(User's visual intent … Property ownership) | [graphics-production.md](graphics-production.md), [ai-assisted-3d.md](ai-assisted-3d.md), [motion-and-3d.md](motion-and-3d.md), [tool-capabilities.md](tool-capabilities.md). 시안 필드(Three same-content temporal/interactive previews)는 세 분기 중 하나: 같은 콘텐츠 동작 시안 세 개와 사용자 결정 / 승인 패턴 / 기존 코드 패턴 재사용(미승인) + 원 코드·동작 동일성·새 표현 아님 판정 근거·변경 상태 검증. 개인 계정 정보 제외, 익명화된 free/included-paid 판단만 |
| Official example comparison | URL / 행동 / 관찰 / 채택 / 대조 결과 표; 접근 불가 시 대체 근거와 한계; Detailed observation evidence(모션·그래픽·3D 상세 관찰 표 링크); Detailed result comparison(모션·그래픽·3D 자산·3D runtime 상세 검증 표 링크) | 새 차트·모션·그래픽/3D 방향이면 필수. 직접 조작 완료 조건은 SKILL.md `### 공통 원칙`. 직접 관찰이 미완료이면 새 방향의 최종 채택과 application source 구현을 보류한다. 접근 가능한 실행본이 있으면 결정을 묻지 않고 직접 조작한다. 접근 불가(URL 응답 실패·로컬 실행 실패의 실제 근거)가 확인된 경우에만 사용자에게 접근 가능한 공식 실행본 확보·공식 소스의 로컬 실행·해당 방향 보류 중 하나를 결정받는다. 대체 자료와 진행 요청은 직접 관찰 완료를 대신하지 않는다. 접근 불가 시 필드에는 URL/로컬 실행 실패 증거·실제 대체 자료·미관찰 행동/성능·사용자가 고른 결정(실행본 확보 / 공식 소스 로컬 실행 / 방향 보류)·관찰 재개 지점을 적고 관찰 완료로 표시하지 않는다. 기존 코드 패턴 재사용(미승인)이면 재사용 근거·변경 결과를 이 표에 연결하고 공식 관찰 이력 부재를 명시한다 |
| Verification evidence | 검사 / 명령·route / 조건 / 결과 / 미실행 사유 표; Before/after screenshots(identical route/viewport/data/theme/state/auth, 각 쌍의 증거 경로 또는 기준선 부재/미실행 근거); Detailed verification results(위 Detailed result comparison 링크를 결과 열에 연결); Performance; Representative task; Intentional findings, deviations, gaps and completion verdict | [verification.md](verification.md) 매트릭스. 모든 구현 모드 필수. 구현 전이면 그 상태를 명시 |
| Feedback correction (when needed) | 기대 / 관찰된 차이 / 원인·근거 / 수정 대상 / 재검증 / 사용자 결정 또는 미확인 표; Reusable instruction defect only if demonstrated | [feedback-improvement.md](feedback-improvement.md) |
| Color | 토큰 표(background, foreground, primary, muted, border, success, warning, danger) × Value, Usage, Contrast evidence | 대비 근거는 실제 측정값. 프로젝트 토큰 이름이 다르면 그 이름을 쓰고 매핑을 적는다 |
| Typography | Korean font, Latin font, Fallback stack, Available weights, Loading strategy, Body size/line-height, Heading ramp, Label/caption, Maximum reading width | 숫자 열은 tabular numerals 여부를 Label/caption 또는 Work UI decisions › Numbers에 적는다 |
| Layout and spacing | Container, Grid, Spacing scale, Dense surfaces, Spacious surfaces, Breakpoints by content failure | breakpoint는 기기 이름이 아니라 콘텐츠가 깨지는 폭 |
| Components | Navigation, Buttons, Forms, Tables/lists, Cards/surfaces, Radius, Border/elevation | 업무 UI의 표·폼 상세는 Work UI decisions에 적고 여기서는 공통 컴포넌트 계약만 |
| Interaction | Hover, Focus-visible, Active, Disabled, Loading, Empty/error/success, Motion timing/easing, Reduced motion | 컴포넌트에 해당하는 상태만 |
| Accessibility | Contrast target, Touch target, Keyboard behavior, Non-color state cues, Heading/landmark rules | 목표와 확인 방법. 기준 수치는 [web-quality.md](web-quality.md) |
| Anti-patterns | 목록 | 이 프로젝트에서 하지 않을 것을 명시(예: 임의 gradient·glow, 카드 중첩) |
| Scope guard | This task may change, must not change, New tokens allowed only when, If approved token rename/rebrand: old → new mapping and rollout order | `small-feature`·보존형 `refactor`에서 필수. 브랜드·전역 토큰 변경 금지를 적는다. rename 매핑은 아래 `## 기존 design-system 이관` 5번 |
| Decision log | Date, Decision, Evidence, Approved by | Approved by는 사용자. 모델·reviewer·subagent를 적지 않는다. Evidence는 제시한 산출물과 사용자 메시지 원문 |

기록 규칙:
- 관찰 가능한 과업 수용 기준을 적고, 만들어낸 만족도 점수를 적지 않는다.
- 사용자가 선택한 것과 에이전트가 추정한 것을 구분한다.
- 승인된 패턴(사용자 결정이 기록된 패턴)을 재사용하면 시안 필드에 "재사용: <패턴 이름>, 기록 위치"를 적고 새 비교를 만들지 않는다. 기록 없는 기존 코드 패턴은 "기존 코드 패턴 재사용(미승인)"으로 구분한다(정의는 SKILL.md `### 공통 원칙`).
- 같은 표가 구현노트·gate 기록에 있으면 복사하지 않고 링크한다.

## 웹 품질

정렬·타이포·밀도·조작 피드백·반응형·성능은 [web-quality.md](web-quality.md)를, 업무 UI의 표·폼·필터·키보드·숫자·권한은 [work-ui-surfaces.md](work-ui-surfaces.md)를 사용한다. 새 값을 제안하기 전에 기존 scale과 브랜드를 보존한다. 선택한 목적의 전문 참조만 읽는다. 이 권고들은 제품·시안 승인을 대체하지 않는다.

## 기존 design-system 이관

`docs/design-system/DESIGN-SYSTEM.md` 같은 기존 문서가 있으면:

1. 경쟁하는 토큰 출처를 만들지 않는다.
2. 그 토큰과 결정을 `DESIGN.md`로 매핑하거나, `DESIGN.md`를 기존 정본을 가리키는 짧은 index로 만든다.
3. CSS를 편집하기 전에 모순을 기록한다.
4. rebrand가 명시적으로 허용하지 않는 한 안정된 토큰 이름을 유지한다.
5. 이름을 바꾼 토큰은 old → new 매핑과 rollout 순서를 `Scope guard`의 해당 필드에 남긴다.

## 레퍼런스

레퍼런스마다 `Direction` 절의 표에 기록한다:

| Reference | Adopt | Reject | Reason |
|---|---|---|---|

관계와 원리를 채택하고, 저작권 있는 자산이나 픽셀 단위 복제는 채택하지 않는다. 레퍼런스 링크는 경험을 설명하는 근거이지 시안 승인이 아니다.
