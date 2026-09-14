---
name: design-workflow
description: Design and improve web interfaces around user tasks, existing design systems, responsive behavior, accessibility, and perceived performance. Use for frontend screens, components, styling, dashboards, landing pages, interactive 3D websites, redesigns, and visual audits; also covers standalone decks and visual reports. Select purpose-specific tools only when needed, preserving real-user interviews and visual-direction/comp approval for new designs. Skip logic-only changes and ordinary tool explanations.
---

# Design Workflow

웹사이트를 사용하는 사람이 **목적을 이해하고, 필요한 정보를 찾고, 다음 행동을 쉽게 완료**하도록 설계한다. 시각 완성도는 정렬·타이포·정보 위계·일관성으로, 체감 품질은 즉각적인 피드백·안정된 레이아웃·명확한 상태·빠른 반응으로 만든다. 만족도 향상을 실측 없이 단정하지 않는다.

정본은 `ai-working/skills/design-workflow/`다. Claude/Codex가 같은 소스를 읽는다. 웹 개발을 기본 경로로 하고, 덱·시각 리포트는 요청 시 [standalone-visuals.md](references/standalone-visuals.md)를 추가로 읽는다. 일반 도구 설명이나 로직 전용 변경에는 디자인 게이트를 적용하지 않는다.

## 작업 분류: 변경 모드와 사이트 목적

| 모드 | 기준 | 보존·승인 범위 |
|---|---|---|
| `new` | 새 제품·신규 랜딩·디자인 정본 없음 | 제품 인터뷰 → 디자인 인터뷰 → 3방향 선택 → 3시안 승인 |
| `rebrand` | 브랜드·색·서체·톤 전면 변경 | 신규와 같은 게이트, 기존 기능·데이터 보존 |
| `refactor` | 기존 UI 구조·위계 개선 | 기존 정체성·동작 보존; 새 시각 세계관 또는 대표 화면 전면 교체는 신규 게이트 |
| `small-feature` | 메뉴·모달·탭·폼·좁은 화면 변경 | 기존 토큰·컴포넌트 재사용, 해당 범위와 상태만 확인 |
| `audit` | 진단·개선안만 요청 | 읽기 전용; source write·설치·issue/commit 금지 |

모호한 요청에만 [mode-selection.md](references/mode-selection.md)를 읽는다. 기존 요청·답변·정본으로 확정 가능한 사실은 다시 묻지 않는다. 작은 작업을 새 제품 인터뷰로 확대하지 않는다.

모드와 별도로 [experience-routing.md](references/experience-routing.md)에서 **주 목적**을 고른다: 업무 UI, 데이터 대시보드, 홍보·콘텐츠, 3D 체험. 혼합 사이트는 페이지/구간별로 분류한다. 한 구간의 3D·모션이 모든 페이지의 기본값이 되지 않게 한다. 목적 선택은 시각 방향 승인을 대신하지 않는다.

## 신규·리브랜딩 절대 게이트

`new`, `rebrand`, 시각 세계관 교체 또는 대표 화면 전면 교체형 `refactor`는 다음 순서를 지킨다.

1. **제품 인터뷰**: 사용자·핵심 과업·차별점·성공/실패 기준을 한 질문씩 확인한다. 새 `PRODUCT.md`를 쓰기 전에 실제 사용자 답변을 최소 한 번 받는다.
2. **디자인 방향 인터뷰**: 브랜드 성격, reference/anti-reference, 밀도, 우선 platform, 접근성 목표를 확인한다. “생각한 디자인 없음”도 생략 사유가 아니다.
3. **시각 방향 세 개**: 이름·핵심 장면·palette·typography·layout 원리가 다른 방향을 제시한다. 사용자의 선택 또는 선택지를 본 뒤의 명시적 위임을 기다린다.
4. **고해상도 시안 정확히 세 개**: 선택된 방향 안에서 composition·density·hierarchy가 다른 시안을 함께 보여주고 `승인 / 조합 / 수정 / 폐기` 결정을 받는다. 같은 레이아웃의 색상 변경만으로 세 개를 채우지 않는다.
5. **구현 잠금 해제**: 선택·채택/비채택 요소·승인 근거를 [gate template](assets/design-gates.template.md)에 기록한 뒤 application source를 수정한다.

필수 게이트가 비면 해당 source write를 멈추고 누락된 질문 하나를 제시한다. `ㄱㄱ`, `알아서`는 아직 보여주지 않은 방향·시안의 승인이 아니다. 모델·reviewer·subagent가 사용자 대신 승인하지 않는다. 기존 승인 범위의 가역적 수정에는 같은 승인을 재요청하지 않는다.

시안·기술 검증용 코드는 분리된 임시 경로에서 만들고 제품 소스에 반영하지 않는다. 동적 사이트의 시안에는 시작/중간/끝 상태 또는 짧은 동작 미리보기를 포함하되 **서로 다른 composition 세 개**라는 기준을 유지한다. 시안의 샘플 데이터·대체 모델은 명시한다.

세 시안은 같은 핵심 콘텐츠·대표 데이터를 사용해 구조 차이를 비교할 수 있게 한다. 웹 시안은 실제 stack에서 구현 가능한 반응형 구조와 주요 상태를 보여준다. HTML로 보여줄 때는 로컬 서버의 응답을 확인한 접근 가능한 URL을 제공하고 해당 작업의 서버를 종료 시 정리한다. 이미 승인된 디자인을 작은 변경 때문에 다시 세 시안으로 만들지 않는다.

## 실행 순서

### 0. 규칙·범위·잠금 확인

- 실제 Git 루트와 `AGENTS.md`, `CLAUDE.md`, 중첩 규칙, HANDOFF, 기존 제품·디자인 정본을 확인한다. 다중 프로젝트 workspace 루트에 설치하지 않는다.
- 구현에는 설치된 `dev-protocol`을 함께 적용한다. 경로를 현재 환경에서 찾고, plugin 번들에만 있다고 가정하지 않는다. 사용자 승인 범위·worktree·구현노트·배포는 그 스킬을 따른다. Git×Supabase×Vercel이면 해당 프로젝트의 `feature-flow`를 적용한다.
- dirty 파일을 보존한다. 모드·범위·주 목적·유지할 계약을 한 줄로 알린다. `audit`는 구현노트나 정본 파일도 만들지 않고 결과를 대화로 보고한다. 사용자가 별도 보고서 저장을 요청하면 그 문서만 저장한다.
- 구현 작업은 gate template을 사용한다. `small-feature`와 보존형 `refactor`의 신규 전용 게이트는 근거와 함께 `N/A`로 표시한다. 가짜 답변·체크 표시로 채우지 않는다.

### 1. 현재 화면과 사용자 과업 조사

[project-audit.md](references/project-audit.md)를 읽는다. stack·버전·토큰·공통 UI와 실제 화면을 함께 확인한다. 핵심 과업 하나를 시작부터 완료까지 따라가며 마찰을 찾는다. 작은 변경은 대상과 존재하는 인접 패턴만 조사한다; 없는 화면이나 문서를 억지로 만들지 않는다.

기존 화면의 정렬·밀도·반응형·상태·console/network 기준선을 남긴다. 새 프로젝트는 기준선 없음으로 기록한다. `audit`는 관찰·검사 결과·추론을 구분해 영향순으로 보고하고 종료한다.

### 2. 요구·경험·디자인 방향 확정

[design-context.md](references/design-context.md)와 선택한 목적의 참조를 읽는다. 발견할 수 없는 제품 결정만 질문한다. 기술 도구 이름보다 원하는 경험을 묻는다: “모델 회전인가, 부품 분해인가, 형태 변형인가”, “이 숫자로 어떤 결정을 하는가”.

기존 `PRODUCT.md`·`DESIGN.md`가 우선이다. 새 정본은 각 승인 시점에 [PRODUCT](assets/PRODUCT.template.md)·[DESIGN](assets/DESIGN.template.md) 템플릿을 채운다. 작은 작업은 기존 정본/구현노트의 해당 부분만 보완한다. 신규 게이트가 필요한 경우 앞의 순서대로 인터뷰·방향·시안을 완료한다.

### 3. 필요한 도구만 선택·준비

[tooling.md](references/tooling.md)를 따른다. **기존 stack → 브라우저/CSS → 기존 라이브러리 → 검증된 추가 의존성** 순서로 판단한다. 도구 후보는 설치 목록이 아니다. 기능·호환성·라이선스·운영 비용은 채택 시 공식 자료로 다시 확인한다.

디자인 보조 스킬은 모드와 부족한 역량에 맞게 선택하고 설치 스크립트의 dry-run을 확인한 뒤 승인된 범위에서 적용한다. 방향/시안 제작에 보조 도구가 필요하면 2단계 중 준비해도 되지만 게이트를 건너뛰지 않는다. 실제 앱 의존성은 구현 잠금 해제 뒤 프로젝트 package manager로 설치한다. `audit`는 설치하지 않는다.

### 4. 구현 계획과 수용 기준

변경/제외 화면, 보존할 기능·데이터·권한·URL·이벤트, 재사용할 컴포넌트, 필요한 UI 상태, 실행할 검증 명령을 정한다. [web-quality.md](references/web-quality.md)를 웹 품질 기준으로 사용한다.

중요한 과업에 대해 **사용자 행동 → 보이는 반응 → 완료 조건**을 짧게 적는다. 예: 기간 필터 변경 → 선택 상태와 조회 상태 표시 → 카드·차트·표에 같은 기간 반영. 이번 목적에 필요한 성능·데이터·3D 기준만 추가한다. 범위 밖 개선은 후속 항목으로 남긴다.

### 5. 구현·정렬·사용감 다듬기

- `Implementation unlocked: yes`와 모드에 필요한 근거를 확인한다.
- 기존 토큰·공통 컴포넌트·semantic HTML을 우선한다. 프레임워크를 React로 가정하지 않는다.
- 구조와 주요 축 → 정보 위계·타이포 → 간격·밀도 → 상태·반응 → 장식 순으로 다듬는다. 그리드에 맞는 숫자뿐 아니라 글자·아이콘의 시각적 정렬도 확인한다.
- 승인된 방향을 화면에 구현한다. 임의의 카드 중첩·gradient·glow·거대한 제목·bounce를 기본값으로 넣지 않는다. 의도된 브랜드 표현은 근거로 유지한다.
- 입력·hover·focus·active·disabled·loading 상태는 **컴포넌트에 해당하는 것만** 구현한다. 명확한 피드백과 오류 복구를 제공하고 실제 성공 전에 성공 표시를 만들지 않는다.
- 기능 계약 변경이 필요하면 영향과 기존 승인 범위를 대조해 `dev-protocol`에 기록한다.

### 6. 실제 검증과 한 번의 개선 검토

[verification.md](references/verification.md)를 따른다. build/lint/test, source/URL detector, 브라우저 desktop/mobile, 핵심 과업 직접 조작과 목적별 검증을 실행한다. 자동 검사는 사용자 평가를 대신하지 않는다.

동일 조건의 전후 화면을 비교하고 발견된 범위 내 문제를 수정한다. 수정한 부분과 영향받는 검증만 반복한다. 해결되지 않은 중요한 실패가 있으면 완료로 표시하지 않는다. 미실행 항목·환경 제약·의도된 예외는 명시한다.

### 7. 완료·인계

사용자 관점으로 **무엇이 쉬워졌는지, 확인할 화면/URL, 실제 검증 결과, 남은 한계**를 보고한다. 사용자 피드백 없이 “만족도 최고”나 임의 점수를 붙이지 않는다. 승인된 미리보기와 실제 결과의 차이를 짧게 설명한다.

디자인 결정은 기존 정본에 남긴다. commit/push·배포·HANDOFF·worktree 정리·운영 후 knowns는 `dev-protocol`에 위임한다. 로컬 변경이나 preview를 운영배포로 간주하지 않는다.

## 완료 기준

- 모드·목적·범위와 diff가 일치하고 필요한 실제 사용자 승인 근거가 있다.
- 기존 디자인/기능 계약을 보존하거나 승인된 변경으로 기록했다.
- 정렬·가독성·반응형·관련 UI 상태와 핵심 과업을 실제 화면에서 확인했다.
- 채택한 도구의 역할·근거·비용/호환성 제약과 목적별 검증 결과를 남겼다.
- build/lint/test·detector·브라우저 검증의 실행 결과와 누락이 구분된다.
- Claude와 Codex가 같은 정본을 참조하며 정본에 새 결정이 반영됐다.
