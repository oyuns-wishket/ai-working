---
name: ssotify
description: Use when the user wants to capture or archive a work setting, workflow, or piece of knowledge as a reusable skill in the public ai-working SSOT. Interviews one question at a time, optionally researches unknowns, then creates and registers the skill without publishing secrets or customer-confidential values.
---

# ssotify — 업무/세팅 SSOT 제너레이터

## Overview
사용자의 업무·세팅·지식을 **다음에 그대로 재사용할 수 있는 공개 SSOT 스킬**로 만든다. 비밀값, 개인 네트워크 식별자, 고객 기밀은 환경 변수·ignored local config·일반화된 placeholder로 분리한다.

## 산출물 위치 / 패턴
- 생성 위치: `$AI_WORKING_ROOT/skills/<name>/` (`AI_WORKING_ROOT`는 현재 checkout이나 설치된 skill link에서 해석)
- 등록: `bootstrap.sh`가 `skills/*` 전체를 `~/.claude/skills/`(Claude)와 `~/.agents/skills/`(Codex 네이티브 스캔 경로)에 자동 직링크 + repo `README.md` 갱신
- 하우스 스타일 골격: 동봉 [`assets/skill-template.md`](assets/skill-template.md)
- 참고 예시는 현재 공개 저장소에서 같은 유형의 skill을 찾아 사용한다.

---

## 진행 절차 — 이 순서대로, **질문은 한 번에 하나씩**

### 1. Intake + 타입 분류
- "무엇을 SSOT화할까요?" 한 줄로 받는다.
- **타입 판별**(사용자에게 확인):
  | 타입 | 무엇 | 중심 구성 | 예 |
  |---|---|---|---|
  | **setup** | 설치/환경설정 | 절차 + 고정값 + 번들 스크립트 + [AI]/[USER] | 개발환경 세팅 |
  | **workflow** | 반복 업무/작업 | 트리거 + 단계 + 정확한 문구/포맷 | 정기 리포트 발행 |
  | **reference** | 지식/정보 아카이빙 | 구조화된 표 + 출처 | (작으면 메모리도 제안) |
- **아주 작은 reference**(한두 사실)면 풀 스킬 대신 **메모리 저장을 제안**(과한 스킬화 방지).

### 2. 적응형 인터뷰 (타입별 체크리스트 — 하나씩 물어본다)
**공통:** 목적 / 트리거 키워드(한·영) / 핵심 고정값(계정·URL·ID·경로·채널 등)
- **setup 추가질문:** 역할 구분 필요?(예 HOST/VIEWER) · 각 단계 **[AI]/[USER]** 분담 · 번들할 스크립트·설정파일 · 권한/GUI 단계의 정확한 클릭경로 · **검증 게이트** · **이미 겪은 실패모드**(트러블슈팅용)
- **workflow 추가질문:** 입력→출력 · 사용 도구/MCP · **정확한 문구/포맷**(토씨까지) · 실제 예시 1개
- **reference 추가질문:** 항목 구조 · 출처 · 갱신 주기/유효기간

> 모르거나 사용자가 답을 못 주는 값은 **추측하지 말 것** → 3번으로.

### 3. 리서치 게이트
- 버전/외부도구/불확실한 값이 있으면 **"리서치해서 채울까요?"** 제안.
- 동의 시 서브에이전트(general-purpose, WebSearch/WebFetch)로 조사 → 결과에 **확정/불확정 표시 + 출처**. 불확정은 스킬에도 불확정으로 표기.

### 4. 초안 확인 (brainstorming 정신)
- 제안 구성(트리거, 섹션, 고정값 표, 단계 개요)을 **간단히 보여주고 승인**받는다. 큰 거면 수정 반영.

### 5. 생성 (하우스 스타일)
동봉 `assets/skill-template.md` 골격으로 `skills/<name>/SKILL.md` 작성. **규약:**
- frontmatter `description`에 **트리거 키워드 풍부히**(한·영 둘 다)
- **SSOT 고정값 표를 한 곳에**(양 많으면 `reference/fixed-values.md`로 분리). "여기서 읽는다" 명시.
- setup이면 **[AI]/[USER] 태그 + 검증 게이트 + 트러블슈팅(실제 실패모드)** 필수
- 번들 스크립트/설정 → `assets/`에, 사용자별 경로는 `<USER>` 플레이스홀더
- 간결·실행가능. **사용자 글로벌 규칙(한국어 대화) 준수.**

### 6. 등록 (Claude × Codex)
- 실행 자산 `chmod +x`
- `"$AI_WORKING_ROOT/bootstrap.sh"` 실행 → `~/.claude/skills/<name>`(Claude)와 `~/.agents/skills/<name>`(Codex)에 자동 직링크. 어댑터·manifest 등록 불필요.
- SKILL.md는 에이전트 중립으로 쓴다. Claude 전용 도구명(`AskUserQuestion` 등)은 글로벌 platform-translation 규칙이 각 플랫폼 등가물로 해석하므로 그대로 써도 된다.
- repo `README.md`의 구조 블록 + 스킬 목록에 한 줄 추가
- 구조 검증: `find skills/<name> -type f`, SKILL.md frontmatter 확인

### 7. 커밋·동기화
- 현재 대화에서 받은 구현·PR·동기화 권한을 재사용한다. commit·push 권한이 없을 때만 한 번 확인한다.
- `.omc/state/*` 같은 무관 런타임 캐시는 **스테이징에서 제외**, 새 스킬 + README만.
- 메시지: `feat(skills): add <name> SSOT`처럼 변경 목적을 설명한다. 고정된 작성자 identity나 모델명을 footer로 넣지 않는다.
- 푸시 후 다른 Mac에서는 `bootstrap.sh --pull`로 같은 정본을 적용한다.

---

## 하우스 스타일 핵심 (생성물 일관성 체크리스트)
- [ ] frontmatter `name`(kebab) + `description`(트리거 한·영 풍부)
- [ ] 고정값은 **표 하나로 SSOT화**, "여기서 읽는다" 명시
- [ ] setup: **[AI]/[USER]** 분담 명확 + 단계별 **검증 게이트**
- [ ] 어렵게 푼 부분은 **⭐ 핵심 섹션**에 "문제→해결→왜 다른 방법 실패" 기록
- [ ] **트러블슈팅 표**(실제 겪은 실패모드)
- [ ] 번들 자산은 `assets/`, 경로 `<USER>` 플레이스홀더
- [ ] 등록(심링크+README) + 승인 범위에 따른 commit·push
