# DESIGN

> Status: draft | approved
> Last verified: YYYY-MM-DD
> Product context: `PRODUCT.md`
> Existing design-system source:

## Direction

- Design intent:
- Brand traits:
- Product density:
- Dominant visual anchor:
- References adopted:
- References rejected:

| Reference | Adopt | Reject | Reason |
|---|---|---|---|

## Web experience decisions

해당 경험이 있으면 관련 필드를 채우고 기존 결정이 있으면 링크한다. 없는 대상만 N/A와 근거로 표시하고 미확인/미실행을 N/A로 감추지 않는다. 게이트·도구 기본값은 [SKILL.md](../SKILL.md)를 따른다.

- Primary purpose and affected routes/sections: 업무 UI / 커머스 / B2C / 데이터 대시보드 / 홍보·콘텐츠 / 그래픽·3D 체험
- Intent analysis: confirmed domain/task/constraints; proposal or reason refinement was unnecessary:
- When proposed: plain experience name/technical term, reference, AI recommendation, refined brief and user decision:
- Core user task and visible completion condition:
- Existing components/tools reused:
- Additional tools and the task/default policy or compatibility reason:
- Official documentation/version/license checked:
- Official example URL and observation date; action → observed result; adopted features: 아래 Official example comparison 기록 링크:
- Reference/approved preview → implementation comparison: present | adapted | absent, evidence and reason: 아래 Official example comparison·Verification evidence 기록 링크:
- Alignment axes and information density:
- Mobile transformation and keyboard behavior:
- Loading, failure recovery, and reduced-motion behavior:
- Performance measurement conditions and target:
- For data: metric/period/unit/source and comparison checks:
- For graphics/3D: link the assisted-production decisions below:

## Motion decisions (web UI)

- Page/section task: work | browse/compare | purchase/book | content/participate | brand:
- Brand tone and recommended motion intent:
- Official observation/adoption/result: 아래 Official example comparison 표 링크:
- Three same-content interactive comparison URLs, AI recommendation and actual user choice, or existing approved preset, or 기존 코드 패턴 재사용(미승인): 원 코드·동작 동일성·새 표현 아님 판정 근거·변경 상태 검증:
- Component/state coverage and selected timing/easing/distance/spring:
- Anime.js/Motion property ownership and installed/reused source:
- If GSAP exception: unavailable feature, official evidence, measured conditions/result, alternative, owned properties, coexistence end condition or retention contract:
- Continuous input/reselection/reset and hover/pin priority; keyboard/touch behavior:
- Reduced motion on initial load and live setting changes; application override policy:
- Cleanup on unmount/route re-entry; measured performance conditions/results:

## Work UI decisions

필수: 업무 표·폼·필터·입력 흐름을 변경하거나 영향받을 때. 없는 요소만 개별 N/A로 표시한다. [work-ui-surfaces.md](../references/work-ui-surfaces.md)의 설계와 [verification.md](../references/verification.md)의 업무 UI 검증을 연결한다.

| Decision | Selected behavior / evidence |
|---|---|
| Task and routes | 핵심 과업·시작/완료·기존 기능/권한/URL 계약 |
| Table columns | 열 순서·주 식별자·텍스트/숫자/단위 정렬·긴 값/절단/전체 값 접근 |
| Bulk actions | 현재 page/전체 조건 선택 구분·선택 수·이동 시 선택 유지·성공/부분 실패·실패 행/사유 |
| Table structure and density | 고정 헤더/열·행 높이·밀도 선택 근거·주/보조 정보·bulk action 위치 |
| Sort/filter/pagination | client/server 범위·기본 정렬·필터 적용/초기화·전체 건수/합계·page 이동/크기/결과 감소·선택 유지/해제 |
| Forms | label·그룹·필수/도움말·오류 위치/요약·검증 시점·입력 보존·저장 중/성공/실패/재시도·중복 제출 방지·자동 저장/이탈 경고·날짜/금액/수량/코드 경계 규칙 |
| Inline editing | 셀/행 편집 단위·진입·dirty·저장/취소·다른 행 클릭 정책·오류/충돌 복구·Enter/F2/Tab/Escape·focus 복귀 |
| Filter bar | 항상 보일 조건·추가 조건·현재 조건 표시·적용 시점·초기화·URL/뒤로가기·모바일 배치 |
| Keyboard and pointer | 대표 과업 순서·Tab/Shift+Tab·Enter/Space/Escape/화살표 계약·focus-visible·dialog 복귀·진입/저장 후 focus·단축키/충돌·연속 입력·pointer/touch 대안 |
| Numbers | 단위·정밀도·반올림·0/null/누락·음수·기간/시간대·page 소계와 전체 합계·원본 대조 |
| Permission and state | 역할별 조회/편집/승인·열 마스킹/행 숨김/기능 제한·읽기 전용/복사·승인 단계·숨김/disabled/거부·loading/empty/no results/error/success·복구 |
| Responsive and zoom | 320 CSS px·200% 확대·표의 별도 scroll/keyboard 접근·필수 정보와 행동 보존 |
| Verification | keyboard+pointer 과업 완료·숫자·정렬/필터/page·인라인 편집·권한별 상태 결과: 아래 Verification evidence 링크 |

## Chart decisions (when charts change)

필수: 차트 작성·디자인 변경·엔진 이관. 차트가 없을 때만 N/A; 기존 승인 패턴은 근거를 재사용하되 변경 상태는 검증한다. 교체 판정은 [data-surfaces.md](../references/data-surfaces.md), 설치·제거는 [tooling.md](../references/tooling.md)를 따른다.

- Bklit component/source reused or added; documented compatibility exception and alternative/user decision if any:
- Installation evidence: app/stack/package manager, verified registry component/command, `components.json` registry/alias/CSS, generated paths/imports, dependency path, lockfile and build evidence:
- Three same-data interactive comparisons, AI recommendation and actual user choice, or approved chart pattern, or 기존 코드 패턴 재사용(미승인): 원 코드·동작 동일성·새 표현 아님 판정 근거·변경 상태 검증:
- Official observation/adoption/result: 아래 Official example comparison 표 링크:
- Metric definition/source, unit/precision/timezone/period/comparison/aggregation/update time; 0/null/missing rules:
- Chart type and task, filters/drill-down/tooltip/legend/export, accessible summary/table and data checks:
- Approved surface/palette/typography/hierarchy/axis/fill/marker/selection/state contract; adopted/rejected elements:
- Selection/hover/pin/reset and chart-summary-table correspondence; period update/geometry continuity:
- Mobile/long legend/first-last point clipping; live reduced motion; representative data/performance evidence:

### Legacy chart engine migration

필수: 레거시 엔진/구 wrapper가 발견됐거나 Bklit 호환성 예외를 판정한 차트 작업. 잠금 해제 전에는 인벤토리·범위·예외 판정·시안 결정·실행 계획을 기록한다. 실제 이관·parity·제거·변경 후 검증과 완료 보고 시 받을 전체 이관 결정은 “구현 후 갱신 예정”으로 표시하며 초기 잠금 해제 조건에 포함하지 않는다. 해당 결과는 완료 판정 전에 갱신한다. 레거시도 호환성 예외도 없으면 조사 범위와 검색 결과를 적고 N/A로 표시한다. 레거시 없이 호환성 예외만 있으면 Target migration에 예외 판정·대안·실제 결정 근거를 기록하고 이관/parity/제거 항목만 N/A로 둔다. `new`는 기준선 화면이 없으므로 대상 화면 이관·parity는 N/A이지만, 같은 저장소에 레거시 엔진이 있으면 인벤토리·판정·전체 이관 제안·공존 기록은 그대로 적용한다. 전체 이관이 남으면 대상 화면의 실제 검증 상태와 전체 미완료를 구분한다.

확인된 개별 차트 예외가 없는 화면은 모든 레거시 차트를 함께 이관한다. 개별 차트의 비호환 예외(필수 기능 부재·실측 성능)가 기록된 화면은 해당 차트에 한해 공존을 허용하고, 예외 범위·의존 비용·재검토 조건을 기록한다. 해당 route는 `기록된 예외`로 집계하며 `이관 완료`나 레거시 import 0건으로 표시하지 않는다. parity 미실행이면 `이관(parity 미실행)`으로 두고 N에 더하지 않으며 [verification.md](../references/verification.md)의 fixture 기반 재대조로 미실행을 해소한 뒤에만 `이관 완료`로 바꾼다. 개별 차트 예외가 있는 route는 `기록된 예외`를 유지하며 이관한 차트의 parity도 따로 기록한다.

| Inventory / decision | Evidence |
|---|---|
| Legacy inventory | 아래 전체 route 인벤토리 + 패키지·버전·alias/import·전용 타입·현재 의존 경로·고유 route 총수 M·별도 사용 파일/import 수 |
| Target migration | 이번 대상 route·보존 데이터/기능·Bklit source·이관 순서·parity 결과 |
| Full migration proposal | 남은 화면·wrapper·기능 차이·이관 순서·중복 비용·제거 조건 |
| Actual user decision | 전체 승인/유예/근거 있는 예외·실제 답변/기존 승인 범위·미결정 사항 |
| Remaining coexistence | 실제 레거시 잔존 사용처·기록된 예외·미처리 이관 대상을 각각 route와 수로 기록; 과도기/예외 이유·후속 범위·재검토/제거 조건 |
| Removal evidence | 제거 대상별 package.json·lockfile·import/require/dynamic import·구 wrapper 검색 명령/범위/건수; 완료이면 각각 0건 |
| Retained dependencies | 현재 Bklit/shadcn 생성 소스의 실제 하위 의존 경로·레거시 계수 제외 근거; Bklit 도입 이전의 프로젝트 자체 recharts 컴포넌트(구 wrapper)와 구분 |
| Post-removal checks | 정리한 wrapper·테마·타입·CSS·설정; typecheck/build/tests·브라우저 parity 결과 |
| Completion claim | 아래 화면별 완료 표·고유 route 기준 N/M·별도 파일/import 수·세 잔여 집계·다음 범위; 과도기 보고는 “부분 적용: N/M 화면 이관, 나머지 제안 중”; 미실행/실패·근거 링크 |

차트 소유 참조의 인벤토리·완료 증거 표를 그대로 사용한다. 화면 이관률 N/M은 고유 route 기준으로 계산한다. 파일·import 수는 별도로 기록한다. “실제 레거시 잔존 사용처”, “기록된 예외”, “미처리 이관 대상”을 구분하며, 미처리 이관 대상만 전체 대상−이관 완료−기록된 예외로 계산한다. N·M에는 공통 wrapper·테마 파일을 화면으로 넣지 않는다. 레거시 import 열은 레거시 패키지/구 wrapper를 import하는 앱 코드 파일 수이며, 생성 chart source의 실제 하위 의존성은 Retained dependencies로 분리한다. 같은 표가 구현노트에 있으면 링크한다.

| 화면/route | 엔진 | 사용처(파일) | 공통 wrapper | 테마/토큰 파일 | 차트 종류 | 비고(export·zoom 등 사용 기능) |
|---|---|---|---|---|---|---|

| 화면/route | 이전 엔진 | 이후 | 대상 화면 레거시 import 건수(파일 수) | parity 결과(수치 대조·필터/기간·tooltip·범례·export·empty/error 상태·키보드/터치·모바일) | 제거된 패키지/파일 | 상태(`이관 완료` / `이관(parity 미실행)` / `이관(parity 실패)` / `기록된 예외: 사유` / `제안 중`) |
|---|---|---|---|---|---|---|

- Remaining usage count:

  | 값 | 계산 | 단위 |
  |---|---|---|
  | 화면 이관률 N/M | `이관 완료` 행 수 / 인벤토리 총 행 수 | 고유 route |
  | 사용처 파일 수 / 공통 wrapper 수 | 인벤토리의 사용처(파일) 열·공통 wrapper 열 집계(현재 시점) | 파일 |
  | 실제 레거시 잔존 사용처 | 레거시 import가 남은 행 수(= `기록된 예외` + `제안 중`; 두 값이 다르면 인벤토리 상태가 틀린 것이므로 상태를 먼저 고친다) | 고유 route |
  | 기록된 예외 | 예외 행 수 + 각 사유 링크 | 고유 route |
  | 미처리 이관 대상 | 총 행 수 − `이관 완료` − `기록된 예외` | 고유 route |
  | 다음 이관 범위 | 전체 이관 제안의 다음 범위·순서 | route 목록 |

- Next migration scope:

| 대상 화면·검사 | 동일 데이터·필터·조건 | 이전 결과 | 이후 결과 | parity 판정·증거 | 미실행/N/A 사유 |
|---|---|---|---|---|---|
| route / 수치·tooltip·범례·export·상태·키보드/터치·모바일별 행 | fixture/기간·viewport·state·theme·auth | 값/동작 | 값/동작 | 일치/승인된 차이/실패/미실행/N/A + 증거 | 없음 또는 제약 |

## Numerical reconciliation

데이터 화면이면 [data-surfaces.md](../references/data-surfaces.md)의 직접 검증에 따라 최소 두 조건(기본 필터/기간 + 변경한 필터/기간)을 기록한다. 차트가 없으면 그 열만 N/A로 표시한다. 같은 표가 기존 기록에 있으면 링크한다.

| 필터/기간 | 원본 집계(쿼리/API 값) | 카드 값 | 차트 값(대표 점) | 표 합계(현재 page / 전체 조건) | 일치 여부 |
|---|---|---|---|---|---|

## Assisted graphics/3D and external capabilities (when relevant)

해당 그래픽/3D·외부 기능이 있으면 필수다. 개인 계정·구독 상세·비밀값 없이 전달 결정만 기록한다. 없는 대상은 N/A와 근거로 표시한다. 기존 코드 패턴을 새 표현 없이 재사용하면 미승인 여부·원 코드·동작 동일성·판정 근거·변경 상태 검증을 시안 필드에 기록한다.

- User's visual intent, realism requirement and requested transformation:
- Section delivery route: video | scroll video/sequence | 2D/2.5D | real-time 3D | hybrid; game-like inputs/rules if relevant:
- Representative action/storyboard and required changes the user can control:
- Agent-owned creation/editing route and available editor/MCP/API:
- Tool/operation capabilities used, evidence type and verification date:
- Included/free execution path, additional-spend decision only if needed:
- If upgrade considered: concrete free/paid outcome difference, user decision, prerequisite and resume point:
- Asset origin/license, required attribution and allowed delivery location:
- Actual multi-angle/model previews, plain-language feedback and adopted changes; scroll scenes require actual scroll/interaction preview with replay (정지 다각도 렌더만으로 통과 불가):
- Three same-content temporal/interactive previews and actual user decision or approved pattern; source-to-web export proof; label substitutes:
- Official observation/adoption/result: 아래 Official example comparison 표 링크:
- Editable source and web asset/export; preserved parts, pivots, materials and clips:
- Renderer and scroll owner; export limitations and hosting choice:
- For media: encoding/frames, playback/seek/cache policy; for games: input/state/reset and required persistence:
- Equivalent fallback or material difference requiring a user decision:
- Actual web URL, mobile/reduced-motion/failed-load and performance evidence:
- Property ownership: scroll progress/camera/clip/time/transform owners, lifecycle cleanup and re-entry evidence:

## Official example comparison

새 차트·모션·그래픽/3D 방향이면 필수. 승인 패턴의 작은 변경이면 기존 관찰·선택을 링크하고 변경 결과를 대조한다. 기록 없는 기존 패턴도 새 표현이 아니면 “기존 코드 패턴 재사용(미승인): 원 코드·동작 동일성·새 표현 아님 판정 근거·변경 상태 검증”을 연결하고 공식 관찰 이력 부재를 명시한다. 새 표현 판정은 [SKILL.md의 공통 원칙](../SKILL.md#공통-원칙)을 따른다. 예제 접근 실패이면 실제 대체 근거와 미관찰 한계를 적는다. 직접 관찰이 미완료이면 새 방향의 최종 채택과 application source 구현을 보류한다. 접근 가능한 실행본이 있으면 결정을 묻지 않고 직접 조작한다. 접근 불가(URL 응답 실패·로컬 실행 실패의 실제 근거)가 확인된 경우에만 사용자에게 접근 가능한 공식 실행본 확보·공식 소스의 로컬 실행·해당 방향 보류 중 하나를 결정받는다. 대체 자료와 진행 요청은 직접 관찰 완료를 대신하지 않는다. 동작 시안·실제 결과 대조는 생략하지 않는다.

| URL | 행동 | 관찰 | 채택 | 대조 결과 |
|---|---|---|---|---|
| 공식 예제·관찰일/대체 근거 | 직접 조작 순서 | 시작·전환·끝 또는 미관찰 한계 | 표현·적용 위치 | 구현 전 / present(반영)·adapted(조정)·absent(누락)·미실행 + route·조건·증거·이유 |

- 접근 불가 시 대체 근거와 한계: URL/로컬 실행 실패 증거·실제 대체 자료·미관찰 행동/성능·실행본 확보/공식 소스 로컬 실행/방향 보류 결정·관찰 재개 지점:
- Detailed observation evidence: [모션](../references/motion-design.md#공식-예제-관찰과-채택-기록)·[그래픽](../references/graphics-production.md#공식-예제-관찰과-채택-기록)·[3D](../references/ai-assisted-3d.md#공식-예제-관찰과-채택-기록)의 상세 관찰 표를 채운 프로젝트 기록 링크:
- Detailed result comparison: [모션](../references/motion-design.md#실제-확인)·[그래픽](../references/graphics-production.md#실행-순서와-결과-대조)·[3D 자산](../references/ai-assisted-3d.md#6-자산-검수와-최종-웹-대조)·[3D runtime](../references/motion-and-3d.md#검증)의 상세 검증 표를 채운 프로젝트 기록 링크:

## Verification evidence

모든 구현 모드에서 [verification.md](../references/verification.md) 매트릭스에 따라 필수. 기존 구현노트에 같은 표가 있으면 링크한다. 구현 전이면 그 상태를 명시한다.

| 검사 | 명령/route | 조건(viewport·data·state·theme·auth) | 결과 | 미실행 사유 |
|---|---|---|---|---|
| 필수 검사·조건별 행 | 실제 명령/조작 | 실제 값; 비해당 N/A | 통과/실패/미실행/N/A·exit code·count·실측·증거 | 없음 또는 이유 |

- Before/after screenshots: identical route/viewport/data/theme/state·auth, 각 쌍의 route·조건·증거 경로; 기준선 부재/미실행이면 근거:
- Detailed verification results: 위 Detailed result comparison의 프로젝트 기록 링크를 결과 열에 연결; 공통 검증 표를 대체하지 않음:
- Performance: device/browser/network/cache/data size/method, before/after measurement and field/lab distinction:
- Representative task: user action → visible response → actual completion:
- Intentional findings, deviations, gaps and completion verdict:

## Feedback correction (when needed)

불만족 피드백이 있으면 [feedback-improvement.md](../references/feedback-improvement.md)에 따라 기록한다. 사용자 답이 없으면 미확인으로 남긴다.

| 기대 | 관찰된 차이 | 원인/근거 | 수정 대상 | 재검증 | 사용자 결정 또는 미확인 |
|---|---|---|---|---|---|
| 요청/승인 시안 | 같은 route·viewport·data·state·theme·auth·장면·행동·기기 조건의 차이 | 취향/코드·자산/성능·권한/workflow | 변경과 승인 범위 | 같은 조건의 전후·영향받는 검사 | 실제 답변 또는 미확인 |

- Reusable instruction defect only if demonstrated: reproduction, proposed owner/change and applicable skill-edit scope:

## Color

| Token | Value | Usage | Contrast evidence |
|---|---|---|---|
| `background` |  |  |  |
| `foreground` |  |  |  |
| `primary` |  |  |  |
| `muted` |  |  |  |
| `border` |  |  |  |
| `success` |  |  |  |
| `warning` |  |  |  |
| `danger` |  |  |  |

## Typography

- Korean font:
- Latin font:
- Fallback stack:
- Available weights:
- Loading strategy:
- Body size/line-height:
- Heading ramp:
- Label/caption:
- Maximum reading width:

## Layout and spacing

- Container:
- Grid:
- Spacing scale:
- Dense surfaces:
- Spacious surfaces:
- Breakpoints by content failure:

## Components

- Navigation:
- Buttons:
- Forms:
- Tables/lists:
- Cards/surfaces:
- Radius:
- Border/elevation:

## Interaction

- Hover:
- Focus-visible:
- Active:
- Disabled:
- Loading:
- Empty/error/success:
- Motion timing/easing:
- Reduced motion:

## Accessibility

- Contrast target: WCAG AA
- Touch target:
- Keyboard behavior:
- Non-color state cues:
- Heading/landmark rules:

## Anti-patterns

-
-
-

## Scope guard

- This task may change:
- This task must not change:
- New tokens allowed only when:
- If approved token rename/rebrand: old → new mapping and rollout order; otherwise N/A:

## Decision log

| Date | Decision | Evidence | Approved by |
|---|---|---|---|
