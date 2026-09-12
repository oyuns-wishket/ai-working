---
name: feature-flow
description: Use when starting feature or fix work in a project that combines Git, Supabase, and Vercel. It normally creates an isolated branch, Preview DB, and preview deployment, while respecting project rules that explicitly select a shared development database. Triggers on "feature-flow", "기능 작업 시작", "브랜치 따서 개발", "개발환경 브랜치", "feat 시작", or "샌드박스 개발".
---

# feature-flow — 브랜치 개발환경 (git × Supabase × Vercel)

## Overview
기능/수정 작업을 **운영(main) 안 건드리고 격리된 브랜치 환경**에서 한다. **플랫폼이 무거운 일을 자동으로** 한다 — 에이전트는 브랜치 따고 PR 열고 머지만 하면, Supabase가 격리 DB 브랜치를, Vercel이 프리뷰 URL을 자동 생성하고 env까지 연결한다.

## 프로젝트 예외를 먼저 확인

작업 전 프로젝트 `AGENTS.md`와 인프라 정본을 읽는다. 프로젝트가 shared development DB를
명시하면 아래 Supabase Preview Branch 절차보다 프로젝트 정책이 우선한다.

**프로젝트가 shared development DB를 명시한 경우:**

- Supabase Automatic Branching을 활성화하거나 PR DB branch를 만들지 않는다.
- Git feature branch와 worktree는 계속 격리하지만 여러 feature와 preview가 하나의 hosted development DB를 공유할 수 있음을 명시한다.
- migration 전 최신 `develop`과 linked migration history를 확인하고 migration file을 같은
  feature branch에 즉시 남긴다. timestamp 충돌이나 미병합 선행 migration이 있으면 중단한다.
- Vercel Preview가 공유 DB를 보므로 이를 격리 환경이라고 보고하지 않는다. 다른 feature의
  schema·데이터 영향을 포함해 검증한다.
- 자동 DB reset·삭제·재시드는 하지 않는다. 운영 DB에는 shared development 정책을 확대 적용하지 않고 프로젝트의 운영 migration gate를 따른다.

상세 경로와 명령은 해당 프로젝트의 infra 문서와 전용 workflow skill을 정본으로 사용한다.

**기본 브랜치 모델: `develop → feat/<x> → develop 머지 → main 머지(배포)`**
```
develop 기준 feat/x 브랜치 → gh pr create --base develop ──(플랫폼 자동)──> Supabase 프리뷰 DB브랜치 + Vercel 프리뷰 URL + env
                                                            └ 그 프리뷰서 개발·테스트
gh pr merge (feat→develop) ──> develop에 통합
… 모아서 gh pr create --base main (develop→main) → merge = 운영 배포 + 마이그레이션 운영 DB 반영
```

## 선행 (프로젝트당 1회, 대시보드 — [USER])
> 이게 "내가 명령 안 해도 자동"의 핵심. 한 번 켜면 그 repo는 PR마다 자동.
1. **Supabase**: 프로젝트 → **Settings → Branches → Enable branching** (Pro 필요 — 있음). GitHub repo 연결.
2. **Vercel**: 프로젝트가 GitHub repo에 연결돼 있으면 PR 프리뷰는 이미 자동. Supabase↔Vercel 통합(Supabase 대시보드 Integrations → Vercel)을 켜면 **프리뷰 배포 env에 브랜치 DB 접속정보가 자동 주입**.
3. (선택) 마이그레이션을 PR에서 자동 적용하려면 Supabase Branching이 PR의 `supabase/migrations`를 자동 실행(기본 동작).
4. **브랜치 시드**: `supabase/seed/*.sql` 작성 + `supabase/config.toml`의 `[db.seed].sql_paths`에 순서대로 등록 → PR 프리뷰 브랜치 **생성 시 1회 자동 시드**(운영 데이터 미복사·운영 무영향). 로컬은 `supabase db reset`으로 동일 적용. 재시드는 PR 닫았다 재오픈. 시드엔 로그인 계정·역할/권한·마스터 등 화면 검증에 필요한 데이터를 둔다. 마이그레이션에 이미 박힌 시드와 중복되지 않게 멱등(`on conflict`)으로.

→ 켜졌는지 확인: `supabase branches list`(linked repo) 또는 Supabase 대시보드 Branches 탭.

## 에이전트 절차 (작업할 때마다 — [AI])
1. **브랜치**: `git checkout develop && git pull` → `git checkout -b feat/<간단명>` (**develop 기준**). main 직접 X.
2. **작업**: 코드 변경. DB 스키마 바꾸면 `supabase migration new <name>`로 마이그레이션 파일 추가(브랜치가 자동 적용).
3. **PR 열기**: `gh pr create --base develop --fill` → **여기서 플랫폼이 자동으로** Supabase 프리뷰 DB브랜치 + Vercel 프리뷰 URL 생성. PR 코멘트에 URL·DB 정보가 달림.
4. **프리뷰에서 검증**: Vercel 프리뷰 URL로 동작 확인. 운영 데이터·DB 무영향.
5. **develop 통합**: `build`·`lint` 실측 통과 후 `gh pr merge --squash` (feat→develop). 프리뷰 브랜치는 머지 시 자동 정리.
6. **운영 배포**: 모은 변경을 `gh pr create --base main`(develop→main) → merge = **운영 배포 + 마이그레이션 운영 DB 반영**. (배포 타이밍 = develop→main 머지)

> 마이그레이션은 Rule 1에 따라 `--dry-run` 결과를 보고하고 승인된 범위와 대조한다. 구체화된 개발 배포 요청에 포함된 비파괴적 개발 migration이나 이미 승인된 운영 범위를 다시 묻지 않는다. 새 파괴적 변경·예상 밖의 범위만 추가 확인하며, 직접 push는 필요한 경우에만 `CONFIRMED=1`로 수행한다.

## 검증 게이트
- PR 열린 뒤 ① Vercel 프리뷰 URL 200 OK ② Supabase Branches 탭에 해당 브랜치 보임 ③ 프리뷰에서 기능 동작.
- 미생성이면 → 선행(대시보드 토글) 미설정. 위 1·2 확인.

## 종료 지식화

운영 배포 검증·HANDOFF까지 끝난 경우에만 completion chain의 **마지막 단계로 `knowns`를 정확히 한 번** 실행한다. PR·개발 배포만 승인받은 작업에는 wiki 선택을 묻지 않고 `dev-protocol`의 개발 배포 closeout을 따른다.

- 이미 `KNOWNS:` 결과가 있으면 중복 호출하지 않는다.
- `knowns`가 제시한 후보를 바탕으로 사용자가 작업물의 의미·목표·기여와 연결점을 확정하고 exact write plan을 승인하기 전에는 wiki를 쓰지 않는다.
- 프로젝트에 명시적으로 연결된 wiki가 없거나 durable delta가 없으면 `knowns`의 skip/no-op 결과를 그대로 보고한다.
- `knowns`를 찾을 수 없거나 blocked이면 브랜치 결과와 별개로 wiki closeout 미완료를 최종 보고에 남긴다.

## 트러블슈팅
| 증상 | 원인 | 대응 |
|---|---|---|
| PR 열어도 DB브랜치 없음 | Supabase Branching 미활성 | 선행 1 (Settings→Branches Enable) |
| PR에 DB branch 없음 | 프로젝트가 명시한 shared DB 정책일 수 있음 | 프로젝트 규칙을 확인하고 shared development DB migration history 대조 |
| 프리뷰가 운영 DB 봄 | Supabase↔Vercel 통합 미연결 | 선행 2 |
| 마이그 안 적용 | migrations 폴더/네이밍 | `supabase/migrations/*.sql` 확인 |
| 브랜치 DB 데이터 비어 있음 | seed 미작성 / `config.toml [db.seed]` 미등록 | `supabase/seed` + `sql_paths` 등록 후 PR 재오픈 |
