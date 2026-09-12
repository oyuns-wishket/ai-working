---
name: design-workflow
description: Analyze an existing web/app project or a standalone visual deliverable, establish or preserve its product and design context, and implement frontend UI, small features, visual refactors, redesigns, rebranding, or presentation decks with mandatory real-user interview, visual-direction, comp approval, and verification gates in Claude Code and Codex. Use for any frontend or visual-output work — screens, components, styling — and for deliverables that are themselves visual artifacts. Triggers on "디자인 작업", "UI 개선", "프론트엔드", "화면 개발", "컴포넌트 개발", "리팩토링", "리브랜딩", "새 디자인", "메뉴 개발", "페이지 디자인", "디자인 시스템", "발표덱", "슬라이드", "제안서", "리포트", "대시보드", "랜딩페이지", "AI 티 제거", "Taste Skill", "Impeccable", "design audit", "redesign", "rebrand", "deck", "slide", "presentation". The team plugin bundles dev-protocol and installs only necessary project-local design tools.
---

# Design Workflow

프로젝트마다 다른 기존 디자인과 업무 맥락을 먼저 읽고, 필요한 범위만 설계·구현·검증한다. 새 제품, 전면 리브랜딩, 기존 UI 리팩토링, 메뉴 하나 같은 소규모 기능을 같은 게이트로 처리하되 서로 다른 변경 강도를 적용한다.

**적용 대상은 시각 결정이 들어가는 모든 작업이다.** 애플리케이션 프론트엔드(화면·컴포넌트·스타일·레이아웃)뿐 아니라, 발표덱·제안서·리포트·대시보드·랜딩처럼 **산출물 자체가 시각물인 작업**도 포함한다. 앱 소스가 아니라는 이유로 게이트를 낮추지 않는다 — 아래 절대 게이트와 모드 체계를 동일하게 적용하고, 검증 항목만 산출물 형태에 맞게 치환한다.

이 스킬의 유일한 SSOT는 `ai-working/skills/design-workflow/`다. 에이전트 홈이나 플러그인에 복사본이 있더라도 이 공개 정본을 수정하고 bootstrap으로 다시 연결한다.

## 신규·리브랜딩 절대 게이트

`new`와 `rebrand`는 아래 순서를 바꾸거나 합치지 않는다.

1. **제품 인터뷰**: 사용자, 구매·사용 목적, 제품의 차별점, 성공·실패 기준을 한 질문씩 확인한다. 새 `PRODUCT.md`를 쓰기 전에 실제 사용자 답변을 최소 한 번 받는다.
2. **디자인 방향 인터뷰**: 브랜드 성격, reference·anti-reference, 정보 밀도, 우선 platform, 접근성 목표를 확인한다. 사용자가 “생각한 디자인이 없다”고 해도 이 단계를 생략하지 않는다.
3. **시각 세계관 선택**: 제품 사실에 맞는 서로 다른 방향 세 개를 이름·핵심 장면·palette·typography·layout 원리와 함께 제시한다. 사용자가 하나를 선택하거나, 세 방향을 본 뒤 명시적으로 선택을 위임할 때까지 기다린다.
4. **고해상도 시안 세 개**: 선택된 세계관 안에서 composition·density·hierarchy가 다른 high-fidelity comp를 정확히 세 개 만든다. 세 개를 한 번에 보여주고 `승인 / 조합 / 수정 / 폐기` 결정을 받는다.
5. **구현 잠금 해제**: 승인된 방향과 comp, 채택·비채택 요소를 구현노트의 gate evidence에 기록한 뒤에만 application source를 수정한다.

필수 gate가 하나라도 비어 있으면 **STOP하고 다음 질문 하나만 제시한 뒤 사용자 응답을 기다린다.** `ㄱㄱ`, `진행해`, `알아서`, `테스트니까 해봐`는 아직 보여주지 않은 방향이나 시안의 승인이 아니다. 모델, subagent, reviewer가 사용자를 대신해 방향이나 comp를 고를 수 없다. 사용자의 선택 위임은 선택지를 실제로 보여준 뒤에만 유효하다.

`assets/design-gates.template.md`를 구현노트에 복사해 gate evidence를 남긴다. `refactor`에서 새 visual world를 만들거나 대표 화면을 전면 교체하면 같은 gate를 적용한다. `small-feature`는 기존 정본을 보존하되 범위·상태·수용 기준을 확인하며, `audit`는 read-only로 끝낸다.

## 핵심 원칙

- 장식보다 제품 목적, 사용자 과업, 정보 위계를 먼저 고정한다.
- 기존 프로젝트에서는 디자인 시스템과 동작을 기본값으로 보존한다.
- 디자인 변경과 기능 변경을 분리한다. 리브랜딩이 아닌 작업에서 비즈니스 로직을 함께 재작성하지 않는다.
- 전역 스킬을 설치하지 않는다. 실제 Git 프로젝트 루트에 Claude와 Codex용 프로젝트 로컬 스킬만 설치한다.
- 스크린샷이나 코드 한쪽만 보지 않는다. 소스, 렌더링 화면, 반응형 상태를 함께 확인한다.
- 자동 검사 결과를 맹목적으로 고치지 않는다. 브랜드 의도와 기존 정본이 우선이며 intentional finding은 근거를 남긴다.

## 모드 선택

| 모드 | 선택 조건 | 기본 변경 강도 | Taste Skill |
|---|---|---|---|
| `new` | 새 제품·신규 랜딩·디자인 정본 없음 | 높음 | `design-taste-frontend` |
| `rebrand` | 브랜드 정체성·색·서체·톤 전면 변경 | 높음 | `redesign-existing-projects` |
| `refactor` | 기존 기능을 유지한 UI 구조·위계 개선 | 중간 | `redesign-existing-projects` |
| `small-feature` | 메뉴, 모달, 탭, 폼, 한 페이지 등 좁은 기능 | 낮음 | 기본 설치 안 함 |
| `audit` | 진단·보고만 요청 | 읽기 전용 | 설치 안 함 |

경계와 대표 예시는 [`references/mode-selection.md`](references/mode-selection.md)를 읽는다. 요청이 여러 모드에 걸치면 가장 좁은 모드로 시작하고 확장 승인을 받는다.

### 앱이 아닌 시각 산출물(발표덱·제안서·리포트)

별도 모드를 만들지 않는다. 산출물 상태로 위 모드에 매핑하고 **같은 게이트를 그대로 통과한다.**

| 상황 | 모드 |
|---|---|
| 새 덱·새 리포트·기존 디자인 정본 없음 | `new` |
| 브랜드·톤을 통째로 갈아엎는 덱 개편 | `rebrand` |
| 기존 덱·리포트의 위계·레이아웃 개선 | `refactor` |
| 기존 덱에 슬라이드·섹션 몇 개 추가 | `small-feature` |
| 기존 덱 진단·개선안만 요청 | `audit` |

- `new`·`rebrand`면 제품(=덱의 목적·청중·핵심 메시지·성공 기준) 인터뷰, 디자인 방향 인터뷰, 시각 세계관 3개, 대표 슬라이드 high-fidelity comp 3개 승인을 **생략하지 않는다.** comp는 전체 덱이 아니라 대표 슬라이드(표지 + 핵심 본문 슬라이드) 기준으로 만들고, 승인된 방향으로 나머지를 전개한다.
- 산출물이 Git 프로젝트 밖이면 `dev-protocol`의 worktree·브랜치 요구는 해당 없음으로 기록하고, 구현노트와 gate evidence는 산출물 디렉토리에 남긴다.
- `PRODUCT.md`/`DESIGN.md` 대신 덱 디렉토리의 정본 문서(예: `DECK.md`)에 목적·청중·메시지·palette·typography·slide grid를 기록한다.

## 실행 절차

### 0. 프로젝트와 작업 규칙 고정

1. `git rev-parse --show-toplevel`로 실제 프로젝트 루트를 확인한다. 다중 프로젝트 workspace 루트에는 설치하거나 디자인 파일을 만들지 않는다. Git 프로젝트가 아닌 단독 산출물(덱·리포트)이면 그 산출물 디렉토리를 작업 루트로 고정하고 상위 디렉토리를 오염시키지 않는다.
2. 프로젝트의 `CLAUDE.md`, `AGENTS.md`, `.claude/rules/`, impl-note, HANDOFF, 기획·브랜드 문서를 읽는다.
3. 구현이면 이 plugin에 함께 포함된 `dev-protocol`을 끝까지 읽고 함께 적용한다. 설치본에서 `dev-protocol`을 찾을 수 없으면 plugin이 불완전한 상태이므로 구현을 시작하지 말고 재설치를 안내한다. Git + Supabase + Vercel 프로젝트면 `feature-flow`를 적용한다.
4. 기존 dirty 파일을 사용자 작업으로 간주하고 보존한다. 자동 stash, reset, overwrite를 하지 않는다.
5. 사용자 요청과 발견한 자료로 모드를 선택해 한 줄로 알린다. 질문 수는 발견 가능한 사실에 맞춰 줄이되, 위 절대 게이트가 요구하는 실제 사용자 답변과 승인은 생략하지 않는다.
6. 구현노트에 `assets/design-gates.template.md`의 gate evidence를 만들고 현재 잠금 상태를 기록한다.

### 1. As-is 증거 수집

[`references/project-audit.md`](references/project-audit.md)를 읽고 다음을 수집한다.

- 제품 목적, 핵심 사용자, 주요 과업
- 프레임워크, package manager, 스타일링 방식, 공통 UI 패키지
- 기존 `PRODUCT.md`, `DESIGN.md`, 디자인 토큰, 테마, 폰트, 로고
- 레이아웃 shell, navigation, 대표 컴포넌트와 상태
- Playwright 기준 스크린샷: 대표 desktop/mobile 화면
- 접근성·반응형·브라우저 console·overflow 기준선
- Impeccable source/URL scan 기준선(설치 없이 `npx` 실행 가능)

`audit` 모드에서는 여기서 보고서를 만들고 파일이나 외부 상태를 변경하지 않는다.

### 2. 필요한 도구만 프로젝트 로컬 설치

[`references/tooling.md`](references/tooling.md)를 읽는다. 먼저 dry-run을 실행한다.

```bash
python3 <skill-root>/scripts/setup_design_tools.py \
  --project <repo> \
  --mode <mode> \
  --json
```

출력된 대상, 명령, 생성 예상 파일을 확인한 뒤 구현 범위가 승인돼 있으면 `--apply`를 추가한다.

```bash
python3 <skill-root>/scripts/setup_design_tools.py \
  --project <repo> \
  --mode <mode> \
  --apply \
  --json
```

- `new`, `rebrand`, `refactor`: 선택한 Taste Skill + Impeccable을 `.claude/skills/`와 `.agents/skills/`에 설치한다.
- `small-feature`, `audit`: Impeccable만 준비한다. 기존 스타일을 벗어날 근거가 있을 때만 Taste Skill을 명시적으로 추가한다.
- 기존 설치가 한쪽 provider에만 있거나 내용이 다르면 자동 덮어쓰지 말고 diff와 선택지를 제시한다.
- 설치된 스킬은 full agent permissions로 동작할 수 있으므로 `SKILL.md`와 생성 diff를 검토한다.
- 새 세션 전이라 자동 발견되지 않으면 설치된 `SKILL.md`를 현재 세션에서 직접 읽고 적용한다.
- tooling 설치와 read-only audit은 구현 승인이 아니다. `new`·`rebrand`에서는 도구를 준비한 뒤 설치된 Impeccable의 `init` → `new-work` → `visualize` 흐름을 따라 절대 게이트를 완료한다.

### 3. 제품·디자인 정본 확정

[`references/design-context.md`](references/design-context.md)를 읽는다.

1. 기존 `PRODUCT.md`, `DESIGN.md`, 디자인 시스템 문서가 있으면 그것을 우선한다.
2. 없으면 제품 인터뷰 답변을 받은 뒤 `assets/PRODUCT.template.md`를 채우고, 시각 세계관이 선택된 뒤에만 `assets/DESIGN.template.md`를 채운다.
3. `small-feature`에서는 정본을 새로 발명하지 않는다. 발견된 컴포넌트·토큰·패턴을 좁게 문서화하고 해당 기능의 scope guard를 남긴다.
4. 레퍼런스가 필요하면 URL·스크린샷을 요청하고, 채택할 요소와 채택하지 않을 요소를 분리한다.
5. 색상·서체·모션은 취향 표현만 남기지 말고 제품 목적과 접근성 근거를 함께 기록한다.

### 4. 변경 계획과 수용 기준

다음을 구현 전에 확정한다.

- 변경 화면과 제외 화면
- 유지할 기능, 데이터, 권한, URL, 이벤트 계약
- 재사용할 기존 컴포넌트와 새로 만들 최소 컴포넌트
- desktop/mobile 상태와 loading/empty/error/disabled/focus 상태
- 디자인 전후 비교 기준
- 실행할 lint, test, build, Playwright, detector 명령

`small-feature`는 관련 메뉴/컴포넌트와 직접 필요한 공통 토큰만 수정한다. 전역 shell, 전체 palette, typography를 함께 바꾸지 않는다.

`new`·`rebrand`와 visual-world 교체형 `refactor`에서는 계획 확정만으로 구현을 시작하지 않는다. 세 comp를 함께 보여준 뒤 받은 사용자 결정을 gate evidence에 기록해야 한다.

### 5. 구현

0. 구현노트의 `Implementation unlocked`가 `yes`인지 확인한다. `no`이거나 증거가 비어 있으면 source write를 중단하고 누락된 gate로 돌아간다.
1. 기존 토큰과 공통 컴포넌트를 먼저 재사용한다.
2. 단순 파생값은 렌더 중 계산하고 React 안정 참조 규칙 등 프로젝트 규칙을 따른다.
3. 시각 위계는 여백 → 굵기 → 크기 → 색 → 장식 순으로 조정한다.
4. 카드 중첩, 의도 없는 gradient/glow, 낮은 대비, bounce, 과도한 radius 같은 상투 패턴을 피한다.
5. 모든 interactive element에 hover, focus-visible, active, disabled, loading 상태를 제공한다.
6. 기능 동작을 바꿔야 하면 디자인 범위와 분리해 계획 이탈로 기록하고 보수적으로 처리한다.

### 6. 이중 검증

[`references/verification.md`](references/verification.md)를 읽고 아래 순서로 검증한다.

1. 프로젝트 lint·test·build
2. `npx --yes impeccable@3.4.0 detect <source-target>`
3. 실행 URL 대상 detector
4. Playwright desktop/mobile screenshot과 console/network 오류
5. keyboard navigation, focus visibility, contrast, touch target, overflow
6. 변경 전후 비교와 `PRODUCT.md`/`DESIGN.md` 일치 여부

detector exit code `2`는 실행 실패가 아니라 finding 존재다. 각 finding을 수정, 의도된 예외, 범위 밖으로 분류하고 근거를 남긴다.

lint·test·build가 없는 단독 산출물은 해당 항목을 그냥 생략하지 않고 아래로 치환해 실제 결과를 남긴다.

- 렌더 검증: 산출물 디렉토리를 로컬 HTTP 서버로 서빙해 브라우저에서 전 슬라이드·전 섹션을 확인한다. 사용자가 다른 기기에 있을 수 있으므로 `open`에만 의존하지 않고 접근 가능한 URL을 전달한다.
- 투사·인쇄 비율(16:9 등)과 실제 발표 환경 해상도에서의 가독성
- 텍스트 overflow, 폰트 fallback, 이미지·차트 누락, 페이지 넘김 깨짐
- 대비·최소 글자 크기 등 접근성 기준

### 7. 완료와 인계

- 변경 파일, 화면, 검증 결과, 남은 intentional finding을 보고한다.
- 구현노트의 `⚠️ DEVIATION`을 리뷰한다.
- 퀴즈를 만들거나 별도 closeout 절차를 복제하지 않는다. 간단 완료 보고, 조건부 배포 범위 선택,
  worktree 정리, HANDOFF, 운영배포 후 `knowns`는 최신 `dev-protocol`의 완료 절차를 그대로 따른다.
- commit/push는 프로젝트 승인·브랜치 규칙을 따른다.
- 실제 운영 배포를 검증한 경우에만 `dev-protocol`의 조건에 따라 `knowns`를 한 번 실행한다. 로컬 작업, preview, 개발 배포, 단독 시각 산출물에는 실행하지 않는다.

## 완료 기준

- 선택한 모드와 실제 diff 강도가 일치한다.
- `new`·`rebrand`는 제품 인터뷰, 디자인 인터뷰, 세 방향 선택, 세 comp 승인, implementation unlock의 실제 사용자 증거가 구현노트에 남아 있다.
- Claude와 Codex가 같은 프로젝트 디자인 정본과 설치 스킬을 읽을 수 있다.
- 기존 동작·데이터·권한 계약이 보존됐거나 승인된 변경으로 기록됐다.
- desktop/mobile과 핵심 UI 상태가 검증됐다.
- lint·test·build 및 detector의 실제 결과가 남아 있다.
- 새 디자인 결정이 `PRODUCT.md`/`DESIGN.md` 또는 기존 정본에 반영됐다.

## 트러블슈팅

| 증상 | 원인 | 대응 |
|---|---|---|
| 한 에이전트에서만 스킬이 보임 | provider 한쪽만 설치 | 두 경로 diff 후 `setup_design_tools.py` 계획을 다시 확인 |
| 스킬 설치 뒤 현재 세션에서 안 보임 | 세션 시작 시 discovery | 설치된 `SKILL.md`를 직접 읽거나 새 세션에서 재개 |
| 작은 메뉴 작업이 전체 리브랜딩으로 번짐 | 모드·scope guard 누락 | `small-feature`로 되돌리고 전역 토큰 변경을 제외 |
| 기존 디자인과 새 파일이 충돌 | 정본 우선순위 미확정 | 기존 문서를 우선하고 차이를 제안 형태로 분리 |
| detector가 종료 코드 2를 반환 | finding 존재 | 실패로 오인하지 말고 finding을 분류 |
| URL 검사가 실행되지 않음 | 앱/브라우저 의존성 미준비 | source scan을 먼저 완료하고 실제 dev URL·브라우저를 준비 |
| 인터뷰 없이 구현이 시작됨 | 짧은 착수 응답을 승인으로 확대 해석 | 추가 write를 멈추고 미승인 초안으로 표시한 뒤 누락된 gate부터 다시 진행 |
| comp를 내부 reviewer가 선택함 | 사용자 승인 gate를 대리 판단 | 세 comp를 사용자에게 함께 제시하고 실제 선택 또는 선택지 제시 후 명시적 위임을 받음 |
