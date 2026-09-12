---
name: generate-spec
description: 범용(도메인 무관) 프로젝트 기획→기능명세 6단계 스킬. Use when starting project planning, creating page/feature specifications, or when user says "프로젝트 기획", "명세 작성", "spec 생성", "generate-spec". ERP/gen-app 파이프라인(erp-core SSOT·델타 모드) 결합 버전은 gen-spec 스킬을 사용.
---

# 프로젝트 기획 명세 생성기

6단계 순차 프로세스를 통해 프로젝트 계획서부터 기능 명세까지의 전체 기획 문서를 마크다운으로 생성한다.

## 프로세스 개요

```
1. 프로젝트 계획서  ←(없음)
2. 메뉴 정의       ← 1
3. 페이지 정의     ← 2
4. 페이지 명세     ← 3 (해당 페이지)
5. 기능 정의       ← 4 (해당 페이지 명세)
6. 기능 명세       ← 5 (해당 기능 정의) + 4 (해당 페이지 명세)
```

## 진입 흐름

### 1. 상태 스캔

`docs/specs/` 폴더를 Glob으로 스캔하여 완료된 단계를 파악한다:

- `docs/specs/01-project-plan.md` 존재 → 1단계 완료
- `docs/specs/02-menu-definition.md` 존재 → 2단계 완료
- `docs/specs/pages/*.md` 존재 → 3단계 (부분) 완료
- `docs/specs/page-specs/**/*.md` 존재 → 4단계 (부분) 완료
- `docs/specs/features/**/*.md` 존재 → 5단계 (부분) 완료
- `docs/specs/feature-specs/**/*.md` 존재 → 6단계 (부분) 완료

### 2. 진행 상태 표시

```
📋 프로젝트 기획 - 현재 진행 상태

  ✅ 1. 프로젝트 계획서    (docs/specs/01-project-plan.md)
  ✅ 2. 메뉴 정의          (docs/specs/02-menu-definition.md)
  ⬜ 3. 페이지 정의
  ⬜ 4. 페이지 명세
  ⬜ 5. 기능 정의
  ⬜ 6. 기능 명세

어떤 단계부터 진행할까요? (기본: N)
```

기본값은 첫 번째 미완료 단계. 단계 3~6은 반복 단위가 있으므로, 진행률도 함께 표시한다 (예: "3. 페이지 정의 (12/46)").

### 3. 단계 선택 및 의존성 확인

사용자가 단계를 선택하면:
1. 해당 단계의 `depends-on` 파일이 존재하는지 확인
2. 없으면: "⚠️ 이전 단계 산출물이 없습니다. N단계를 먼저 진행하는 것을 권장합니다. 그래도 진행할까요?"
3. 있으면: 즉시 해당 단계 진행

## 단계별 진행 루프

### 단일 산출물 단계 (1~2단계)

1~2단계는 산출물이 하나이므로 메인 에이전트가 직접 처리한다:

1. **템플릿 로드**: 이 스킬 디렉토리의 `templates/0N-xxx.template.md`를 Read
2. **의존 파일 로드**: frontmatter `depends-on`에 명시된 파일들을 Read
3. **대화를 통한 초안 작성**: 템플릿의 각 섹션을 순서대로 사용자와 대화하며 채워간다. 사용자에게 질문하고, 답변을 바탕으로 섹션을 작성한다.
4. **초안 제시**: 완성된 마크다운 초안을 사용자에게 보여준다
5. **피드백 루프**: 사용자 피드백 반영 → 수정 → 재제시 (승인까지 반복)
6. **파일 저장**: 승인 시 Write 도구로 md 파일 저장
7. **다음 안내**: "다음 단계로 진행할까요?"

### 반복 단위가 있는 단계 (3~6단계) — 병렬 서브에이전트 필수

> **핵심 규칙**: 3~6단계에서 처리할 항목이 2개 이상이면 **반드시 Agent 도구로 병렬 서브에이전트를 디스패치**한다.
> 항목마다 멈추거나 "다음 항목으로 진행할까요?"를 묻지 않는다. **절대로.**

#### 실행 흐름

```
1. 사용자에게 해당 단계 전체 진행 의사 확인 (1회만)
   예: "4단계 페이지 명세를 시작합니다. 미완료 12개 페이지를 병렬로 작성합니다. 진행할까요?"
2. 대상 항목 목록 산출 (의존 파일에서 추출)
3. 이미 완료된 항목 제외
4. 남은 항목을 배치로 묶어 병렬 서브에이전트 디스패치
5. 모든 서브에이전트 완료 후 결과 요약 제시
6. 사용자 피드백 수렴 → 수정 필요 시 해당 항목만 재디스패치
7. "다음 단계로 진행할까요?" (단계 전환 시에만 질문)
```

#### 배치 크기

- **최대 동시 서브에이전트**: 5개
- 항목이 5개 초과 시: 5개씩 배치로 나누어 순차 디스패치 (배치 내부는 병렬)
- **배치 간에도 멈추지 않고 연속 진행한다.** 중간에 사용자 확인을 요청하지 않는다.

#### 서브에이전트 프롬프트 구성

각 서브에이전트에게 전달할 프롬프트에 **반드시** 포함할 내용:

1. **역할**: "프로젝트 기획 명세 작성 에이전트"
2. **템플릿 경로**: Read로 로드할 템플릿 파일의 절대 경로
3. **의존 파일 경로**: Read로 로드할 의존 산출물의 절대 경로 (모두 명시)
4. **출력 파일 경로**: Write로 저장할 파일의 절대 경로
5. **품질 기준**: 해당 산출물의 최소/목표 토큰 범위 (한글 기준 1토큰 ≈ 3.5자)
6. **네이밍 규칙**: 번호, kebab-case 변환 규칙
7. **frontmatter 규칙**: stage, depends-on, created-at, status 등
8. **핵심 지시**: "템플릿을 Read로 로드하고, 의존 파일을 Read로 로드한 뒤, 템플릿 구조에 따라 빈 섹션 없이 완성된 마크다운을 작성하여 Write로 저장하라. 사용자에게 질문하지 말고 의존 파일의 내용을 기반으로 자율적으로 판단하여 작성하라."

#### 서브에이전트 호출 예시 (4단계)

```
# 미완료 페이지가 5개인 경우
# 반드시 하나의 메시지에서 5개의 Agent 도구 호출을 동시에 보낸다

Agent(description="페이지 명세: 알림 센터", subagent_type="general-purpose", prompt="...")
Agent(description="페이지 명세: 도움말", subagent_type="general-purpose", prompt="...")
Agent(description="페이지 명세: 대시보드", subagent_type="general-purpose", prompt="...")
Agent(description="페이지 명세: 설정", subagent_type="general-purpose", prompt="...")
Agent(description="페이지 명세: 정산", subagent_type="general-purpose", prompt="...")
```

#### 단계별 서브에이전트 입력/출력

| 단계 | 서브에이전트 단위 | 입력 (Read) | 출력 (Write) |
|------|------------------|-------------|-------------|
| 3 | 하위 메뉴 1개 | 템플릿 + `02-menu-definition.md` | `pages/NN-xxx.md` |
| 4 | 페이지 1개 | 템플릿 + 해당 `pages/NN-xxx.md` | `page-specs/NN-xxx/00-page-spec.md` |
| 5 | 페이지 1개 | 템플릿 + 해당 `page-specs/NN-xxx/00-page-spec.md` | `features/NN-xxx/*.md` |
| 6 | 기능 1개 | 템플릿 + 해당 `features/NN-xxx/MM-yyy.md` + 해당 `page-specs/NN-xxx/00-page-spec.md` | `feature-specs/NN-xxx/MM-yyy.md` |

#### 3단계 세부

메뉴 정의(2단계)를 읽고 하위 메뉴 목록을 추출. 각 하위 메뉴마다 페이지 정의 md를 병렬 생성. 하위 메뉴가 없는 대메뉴는 대메뉴 자체가 1개 페이지 정의.

#### 4단계 세부

페이지 정의(3단계) 파일 목록을 Glob으로 수집. 각 페이지마다 서브에이전트를 디스패치하여 페이지 명세를 생성.

#### 5단계 세부

페이지 명세(4단계) 파일 목록을 Glob으로 수집. 각 페이지마다 서브에이전트를 디스패치하여 해당 페이지의 기능들을 정의.

#### 6단계 세부

기능 정의(5단계) 파일 목록을 Glob으로 수집. 각 기능마다 서브에이전트를 디스패치. 페이지 명세(4단계)도 함께 Read 경로에 포함.

### 멈춤 금지 규칙 (CRITICAL)

다음 행위는 **절대 금지**한다:

- ❌ 항목 1개 완료 후 "다음 항목으로 진행할까요?" 질문
- ❌ 배치 완료 후 다음 배치 진행 전 사용자 확인 요청
- ❌ 서브에이전트 없이 메인 에이전트가 항목을 하나씩 순차 처리
- ❌ "나머지는 다음에 하시겠습니까?" 류의 중단 유도 질문
- ❌ 항목 수가 많다는 이유로 일부만 처리하고 멈추기
- ❌ "시간이 오래 걸릴 수 있습니다" 경고 후 사용자 재확인 요청

다음 행위만 **허용**한다:

- ✅ 단계 최초 진입 시 1회 의사 확인
- ✅ 단계 전체 완료 후 다음 단계 전환 질문
- ✅ 사용자가 **명시적으로** 중단을 요청한 경우에만 중단

사용자가 "특정 메뉴/페이지만 먼저" 요청하면 해당 항목만 선택적으로 진행 가능. 이 경우에도 선택된 항목이 2개 이상이면 병렬 디스패치한다.

## 산출물 디렉토리 구조

```
docs/specs/
  01-project-plan.md                        # 1단계
  02-menu-definition.md                     # 2단계
  pages/
    01-notification-center.md               # 3단계
    02-help.md
    ...
  page-specs/
    01-notification-center/
      00-page-spec.md                       # 4단계
    02-help/
      00-page-spec.md
    ...
  features/
    01-notification-center/
      01-notification-list-view.md          # 5단계
      02-notification-rule-settings.md
    02-help/
      01-guide-list-and-detail.md
      ...
  feature-specs/
    01-notification-center/
      01-notification-list-view.md          # 6단계
    02-help/
      01-guide-list-and-detail.md
      ...
```

## 네이밍 규칙

- **번호**: 메뉴 정의의 sortOrder 기반, 2자리 zero-pad (`01`, `02`, ...)
- **파일명**: 영문 kebab-case. 한글 메뉴/페이지/기능명을 의미 기반으로 번역.
  - 예: 알림 센터 → `notification-center`
  - 예: 정산 용어 사전 검색 및 열람 → `glossary-search`
- **폴더명**: 페이지와 동일 번호+이름 사용.

## frontmatter 규칙

모든 산출물 md 파일의 최상단에 YAML frontmatter를 포함한다:

```yaml
---
title: "알림 목록"
stage: "page-definition"
depends-on:
  - "docs/specs/02-menu-definition.md"
created-at: YYYY-MM-DD
status: draft | review | approved
---
```

`stage` 허용값: `project-plan`, `menu-definition`, `page-definition`, `page-spec`, `feature-definition`, `feature-spec`

## 품질 게이트

각 산출물 저장 전 분량을 검증한다 (한글 기준 1토큰 ≈ 3.5자):

| 산출물 | 최소 토큰 | 목표 범위 | 최대 토큰 | 미달 시 |
|--------|----------|----------|----------|--------|
| 프로젝트 계획서 | 1,500 | 2,000~3,000 | - | 섹션 누락 경고 |
| 메뉴 정의 | 1,000 | 1,500~2,500 | - | 메뉴 상세 부족 경고 |
| 페이지 정의 | 300 | 500~800 | - | 기능 목록 부족 경고 |
| 페이지 명세 | 2,000 | 2,500~3,500 | - | 섹션 누락 보완 요청 |
| 기능 정의 | 200/기능 | 300~500/기능 | - | 설명 부족 경고 |
| 기능 명세 (필수 1~8) | 4,000 | 4,500~7,000 | 12,000 | 미달: 보완 요청 / 초과: 기능 분할 검토 |

글자수로 환산: 산출물의 `length(content)` 값을 3.5로 나누어 토큰 추정.

## 각 단계 템플릿 참조

| 단계 | 템플릿 파일 | 진입 시 Read |
|------|-----------|-------------|
| 1. 프로젝트 계획서 | `templates/01-project-plan.template.md` | 이 파일만 |
| 2. 메뉴 정의 | `templates/02-menu-definition.template.md` | 이 파일 + 01 산출물 |
| 3. 페이지 정의 | `templates/03-page-definition.template.md` | 이 파일 + 02 산출물 |
| 4. 페이지 명세 | `templates/04-page-spec.template.md` | 이 파일 + 해당 03 산출물 |
| 5. 기능 정의 | `templates/05-feature-definition.template.md` | 이 파일 + 해당 04 산출물 |
| 6. 기능 명세 | `templates/06-feature-spec.template.md` | 이 파일 + 해당 05 산출물 + 해당 04 산출물 |

**중요**: 템플릿 파일은 반드시 Read 도구로 로드한다. 기억에 의존하지 않는다.
