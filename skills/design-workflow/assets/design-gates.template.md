# Design gate evidence

기존 구현노트 안에서 사용한다. 승인 판정·게이트 순서·도구 기본값은 [SKILL.md](../SKILL.md)를 따른다. 모델 추론·reviewer/subagent 결정·선택지나 시안을 제시하기 전 사용자 발언을 승인으로 채우지 않는다. 각 기록은 실제 사용자 답변과 제시한 산출물을 연결한다. 질문과 AI 추천은 `Question`(또는 해당 AI recommendation 필드)에, 사용자 발화는 `Real user answer`에 원문 그대로, 채택 결과는 해당 `Confirmed`/`Adopt` 필드에 기록한다. 요약 확인의 제시문 원문도 `Question`에 두고 사용자 답변 원문과 섞지 않는다. `User choice, or explicit delegation after viewing`도 사용자 발화 원문만 기록하는 필드다.

## Mode and lock

필수: 모든 구현 모드. `audit`는 잠금을 유지하며 이 파일을 생성하지 않고 필요한 진단만 대화로 보고한다.

| Field | Evidence |
|---|---|
| Mode | `new / rebrand / refactor / small-feature` 중 하나 |
| Application source writes | `locked / unlocked` |
| Primary purpose and scope | 업무 UI / 커머스 / B2C / 데이터 대시보드 / 홍보·콘텐츠 / 그래픽·3D 체험; 대상 route·구간 |
| Existing user request/approval and design source | 실제 요청·기존 승인·정본 경로 |
| Required gate set | full: new/rebrand/시각 세계관 교체/대표 화면 전면 교체형 refactor; scoped: small-feature/보존형 refactor |
| Scoped acceptance evidence | 허용/제외 범위·보존 계약·관련 상태·행동 → 반응 → 완료 조건·정본 |
| Intent refinement | 충분히 명확/기존 근거 재사용 또는 쉬운 경험 제안·보완 요청문과 실제 결정 |

scoped 작업이면 아래 Product interview·Design-direction interview·Visual-world decision·High-fidelity comps를 `N/A`와 기존 정본/보존 근거로 기록한다. **이는 신규 전용 게이트의 N/A이며 조사·새 표현의 동작 시안·검증 생략이 아니다.** 새 모션·차트·그래픽·3D 방향이면 같은 데이터/콘텐츠의 **동작 시안 정확히 세 개**를 다음 Relevant experience evidence에 기록한다. 새 시각 세계관이나 대표 화면 전면 교체이면 full 게이트를 적용한다. scoped 작업에서 새 표현 없이 승인 패턴 또는 (새 표현 판정에 따른) 기존 코드 패턴을 재사용하면 **동작 시안만** 생략한다. 승인 여부·재사용 근거(승인 패턴 이름·기록 위치, 또는 원 코드·동작 동일성·판정 근거)·보존 범위·신규 전용 항목의 N/A를 gate template에 기록하고 구현 잠금을 해제한다. full 게이트는 이 분기로 생략하지 않는다.

## Relevant experience evidence

필수: 모든 구현 모드에서 변경하거나 영향받는 경험. 실제 해당 경험이 없을 때만 행별 `N/A + 근거`를 허용한다. full 작업은 같은 세 composition에 통합하고 별도 연속 승인 묶음을 만들지 않는다. 아래 모든 시안/패턴 필드의 분기는 새 표현의 시안 세 개·사용자 결정, 승인 패턴 재사용, 새 표현이 아닌 기존 코드 패턴 재사용(미승인) 중 하나다. 재사용이면 변경 상태 검증을 생략하지 않는다.

잠금 해제 전에는 인벤토리·범위·예외 판정·시안 결정·실행 계획을 기록한다. 실제 이관·parity·제거·변경 후 검증과 완료 보고 시 받을 전체 이관 결정은 “구현 후 갱신 예정”으로 표시하며 초기 잠금 해제 조건에 포함하지 않는다. 해당 결과는 완료 판정 전에 갱신한다.

| Experience | Evidence |
|---|---|
| Motion | 과업/브랜드 추천·같은 콘텐츠의 동작 시안 정확히 세 개·AI 추천·실제 사용자 결정 또는 기존 승인 preset·변경 상태 검증 또는 기존 코드 패턴 재사용(미승인): 원 코드·동작 동일성·새 표현 아님 판정 근거·변경 상태 검증; Anime.js 연출이면 대상 속성 소유권·Motion과의 분담·GSAP 예외 근거([DESIGN Motion decisions](DESIGN.template.md#motion-decisions-web-ui) 링크; GSAP이 없으면 그 예외 필드만 N/A) |
| Charts | Bklit 경로/확인한 호환성 예외·같은 데이터의 동작 시안 정확히 세 개·AI 추천·실제 결정 또는 승인 패턴·변경 상태 검증 또는 기존 코드 패턴 재사용(미승인): 원 코드·동작 동일성·새 표현 아님 판정 근거·변경 상태 검증; 레거시 엔진 인벤토리·이관 화면·parity·전체 이관 제안·사용자 결정(또는 기록된 예외)은 아래 Legacy chart engine migration 링크 |
| Legacy chart engine migration | 인벤토리(패키지·wrapper·전체 사용 route)·대상 화면 이관·parity·전체 이관 제안·실제 사용자 결정·고유 route 기준 이관률 N/M·별도 파일/import 수·실제 레거시 잔존 사용처/기록된 예외/미처리 이관 대상·잔여 route/재검토 조건·제거 증거 링크; 상태는 `이관 완료 / 이관(parity 미실행) / 이관(parity 실패) / 기록된 예외: 사유 / 제안 중`; `이관(parity 미실행)`·`이관(parity 실패)`·`기록된 예외`는 N에서 제외. 레거시도 호환성 예외도 없으면 조사 근거와 N/A; 레거시 없이 호환성 예외만 있으면 판정·대안·실제 결정을 기록하고 이관/parity/제거만 N/A |
| Work UI evidence | 표·폼·필터·키보드·포인터 과업·숫자/정렬/page·인라인 편집/저장·320px/200%·권한별 검증 결과 링크; 없는 요소만 개별 N/A |
| 3D | 새 방향이면 같은 콘텐츠의 동작 시안 정확히 세 개·AI 추천·실제 결정 또는 승인 패턴; 실제 모델 다각도/장면 검수·사용자 피드백·에이전트 수정/export/web 계획·placeholder 표시; scroll 장면은 actual scroll/interaction preview with replay(실제 scroll/interaction 미리보기·replay) 필수; 정지 다각도 렌더만으로 통과 불가 |
| Graphics | 전달 경로·같은 콘텐츠 동작 시안 정확히 세 개 또는 승인 패턴·source-to-web sample·게임 입력/규칙·mobile 대안·사용자 결정 |
| External capability | 사용한 free/included-paid 작업·근거/날짜·전달 권리/호스팅·미해결 선행조건; 개인 계정 정보 제외 |

확인된 개별 차트 예외가 없는 화면은 모든 레거시 차트를 함께 이관한다. 개별 차트의 비호환 예외(필수 기능 부재·실측 성능)가 기록된 화면은 해당 차트에 한해 공존을 허용하고, 예외 범위·의존 비용·재검토 조건을 기록한다. 해당 route는 `기록된 예외`로 집계하며 `이관 완료`나 레거시 import 0건으로 표시하지 않는다. `new`는 기준선 화면이 없으므로 대상 화면 이관·parity는 N/A이지만, 같은 저장소에 레거시 엔진이 있으면 인벤토리·판정·전체 이관 제안·공존 기록은 그대로 적용한다.

상세 필드와 판단은 [work UI](../references/work-ui-surfaces.md), [차트 교체](../references/data-surfaces.md), [검증](../references/verification.md)을 따른다. [DESIGN의 Official example comparison](DESIGN.template.md#official-example-comparison)에 관찰·채택·대조 결과를 기록했으면 아래 표에서 해당 기록을 링크한다. 아래 표는 새 표현이면 필수이며 승인 패턴 재사용이면 기존 관찰을 링크하고 변경 결과를 대조한다. 기록 없는 기존 코드 패턴도 새 표현이 아니면 위의 미승인 재사용 근거와 변경 결과를 이 표에 연결하고, 공식 관찰 이력 부재를 명시한다. 표현 대상 자체가 없을 때만 N/A다. 새 표현 판정은 [SKILL.md의 공통 원칙](../SKILL.md#공통-원칙)을 따른다.

| URL | 행동 | 관찰 | 채택 | 대조 결과 |
|---|---|---|---|---|
| 공식 예제·관찰일/대체 근거 | 직접 조작 순서 | 시작·전환·끝 또는 미관찰 한계 | 표현·적용 위치 | 구현 전 / present(반영)·adapted(조정)·absent(누락)·미실행 + route·조건·증거·이유 |

- 접근 불가 시 대체 근거와 한계: URL/로컬 실행 실패 증거·실제 대체 자료·미관찰 행동/성능·실행본 확보/공식 소스 로컬 실행/방향 보류 결정·관찰 재개 지점:
- Observation and detailed verification evidence: [DESIGN 관찰 기록](DESIGN.template.md#official-example-comparison)과 [모션](../references/motion-design.md#실제-확인)·[그래픽](../references/graphics-production.md#실행-순서와-결과-대조)·[3D 자산](../references/ai-assisted-3d.md#6-자산-검수와-최종-웹-대조)·[3D runtime](../references/motion-and-3d.md#검증)의 해당 상세 표를 채운 프로젝트 기록 링크:

동작을 직접 확인할 수 없으면 관찰 미실행을 밝히고 실제 대체 근거를 적는다. 직접 관찰이 미완료이면 새 방향의 최종 채택과 application source 구현을 보류한다. 접근 가능한 실행본이 있으면 결정을 묻지 않고 직접 조작한다. 접근 불가(URL 응답 실패·로컬 실행 실패의 실제 근거)가 확인된 경우에만 사용자에게 접근 가능한 공식 실행본 확보·공식 소스의 로컬 실행·해당 방향 보류 중 하나를 결정받는다. 대체 자료와 진행 요청은 직접 관찰 완료를 대신하지 않는다. 정지 이미지·문서 읽기·설치 성공을 동작 관찰 또는 시안 승인으로 채우지 않는다.

## Product interview

필수: full 게이트. scoped는 기존 정본·보존 범위 근거와 N/A; audit는 작성 금지.

- Status: `pending / complete / N/A + reason`
- Question: 질문 원문; 요약 확인이면 항목별 값·추정 근거를 열거한 요약 원문:
- AI recommendation (if given):
- Real user answer or explicit summary approval (사용자 발화 원문만; 요약 확인은 항목별 값·추정 근거를 열거한 요약 뒤의 답만; 요약 원문은 Question, 사용자 원문은 이 필드에 기록):
- Confirmed user, job, differentiation, success and failure criteria:

## Design-direction interview

필수: full 게이트. scoped는 기존 정본·보존 범위 근거와 N/A; audit는 작성 금지.

- Status: `pending / complete / N/A + reason`
- Question: 질문 원문; 요약 확인이면 항목별 값·추정 근거를 열거한 요약 원문:
- AI recommendation (if given):
- Real user answer (사용자 발화 원문만; 요약 확인은 위 Question의 열거 항목에 대한 답만):
- Confirmed brand traits, reference/anti-reference, density, platform and accessibility:

## Visual-world decision

필수: full 게이트. scoped는 기존 정본·보존 범위 근거와 N/A; audit는 작성 금지.

- Status: `pending / complete / N/A + reason`
- Three distinct worlds shown (names, artifacts and differences):
- AI recommendation and reason shown with the options:
- User choice, or explicit delegation after viewing (사용자 발화 원문만; 위임이면 AI 추천안 제시 뒤의 발화만; 산출물 제시 전 발화 무효):
- Adopt:

## High-fidelity comps

필수: full 게이트의 선택된 방향 안에서 정확히 3개. scoped 신규 전용 항목은 N/A이며 새 표현의 3개 동작 시안은 Relevant experience evidence에 기록; audit는 작성 금지.

- Status: `pending / complete / N/A + reason`
- Exactly three comps shown together: 응답 확인한 동작 시안 URL; 움직이는 요소가 없는 정적 화면만 이미지 허용:
- Same core content/data; different composition/density/hierarchy:
- Relevant direct interactions (click/filter/scroll/replay/reset) and mobile alternative:
- AI recommendation and reason:
- User decision: `approve(승인) / combine(조합) / revise(수정) / reject(폐기)`
- Real user answer, or explicit delegation after viewing (사용자 발화 원문만; 위임이면 AI 추천안 제시 뒤의 발화만; 산출물 제시 전 발화 무효):
- Delegation after viewing stage 4: 세 시안 제시 시점/URL·함께 제시한 AI 추천·그 뒤 사용자 원문/시점·위임으로 채택한 안; 위임 없으면 N/A:
- Adopt:
- Reject:
- If combine/revise: precise accepted elements, unresolved elements and revised preview/decision evidence:
- Revised/combined comp shown and approved (path/URL, user answer):
- Partial approval: 승인 범위·채택 요소·미승인/미해결 범위·각 범위의 잠금 상태:

### 시안 결정과 잠금 판정

아래 표는 full의 4단계와 scoped의 새 표현 동작 시안에 동일하게 적용한다. 승인 판정의 정본은 [SKILL.md의 부분 승인과 재제시](../SKILL.md#부분-승인과-재제시)다.

| Decision | 다음 행동 | 잠금 상태 |
|---|---|---|
| `reject` | 폐기 근거를 기록하고 새 시안 정확히 세 개 또는 방향 재선택 | 잠금 유지 |
| `revise` | 수정 시안 하나를 재제시하고 실제 사용자 결정을 기록 | 재제시 후 승인까지 잠금 유지 |
| `combine` | 채택 요소·구현 범위·미승인 범위를 명시하고 조합 시안 하나를 재제시해 사용자 승인 기록 | 조합안 재제시·승인까지 잠금 유지; 그 증거가 있는 combine만 승인 범위 해제 가능 |
| `approve` | 제시한 시안 이후의 실제 사용자 원문·채택안·구현 범위를 연결 | 나머지 필수 게이트도 충족한 승인 범위만 해제 가능 |

시안 제시 후 AI 추천을 본 사용자의 명시적 위임이면 채택안은 `Adopt`, 사용자 원문은 해당 답변 필드에 기록하고 `approve`로 처리한다. `승인`만으로 대상이 유일하게 특정되는 경우(안이 하나 남았거나 직전에 특정 안을 재제시)에만 해당 안을 승인 처리한다. 여러 안이 남아 채택 대상이 불명확하면 승인할 안 하나를 확인하며 잠금을 유지한다. AI 추천안이 명시된 뒤의 `승인`·`추천대로`는 추천안 승인이다. 부분 승인에서 미승인 범위는 계속 잠근다. `complete`나 잠금 해제를 먼저 기록한 뒤 증거를 채우지 않는다.

## Implementation unlock

필수: 모든 구현 모드. audit는 `no`를 유지하고 이 파일을 생성하지 않는다. 증거 없는 N/A로 잠금을 풀지 않는다.

- Required gates and valid scoped N/A reviewed; 새 방향이면 공식 실행 예제 직접 관찰 완료 증거(미완료이면 잠금 유지):
- combine/revise이면 조합/수정한 시안 하나의 재제시·사용자 승인 증거(또는 해당 없음):
- Approved implementation scope; any pending/unapproved scope remains locked:
- Implementation unlocked: `yes / no`
- Evidence for unlock (actual user decisions and artifact links):

사용자와 직접 대화하는 에이전트만 원문 답변·승인 해석·잠금 해제를 기록한다. Reviewer/subagent는 검증·추천을 제공하며 위 필드를 승인으로 채우지 않는다. 부분 승인·위임은 SKILL.md의 재제시·추천안 조건을 모두 확인한다.

## Verification evidence

필수: 모든 구현 모드의 구현 후 [verification.md](../references/verification.md) 매트릭스. 구현 전에는 `구현 전`으로 표시하며 완료로 체크하지 않는다. 실제 검사 대상 부재만 N/A, 환경 제약은 미실행이다.

| 검사 | 명령/route | 조건(viewport·data·state·theme·auth) | 결과 | 미실행 사유 |
|---|---|---|---|---|
| 각 필수 검사·조건별 행 | 실제 명령/조작 | 실제 값; 비해당 N/A | 통과/실패/미실행/N/A·exit code·count·실측·증거 | 없음 또는 구체적인 이유 |

- Parity/removal evidence: 관련 DESIGN의 Chart decisions 링크 또는 대상 없음 근거:
- Detailed verification results: 위 Observation and detailed verification evidence의 프로젝트 기록 링크를 결과 열에 연결; 공통 검증 표를 대체하지 않음:
- Intentional findings, deviations and remaining scope:
- Completion verdict and unverified conditions:
