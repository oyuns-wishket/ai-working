# Worker capability catalog

이 문서는 설치 목록이 아니라 선택 카탈로그다. Lead는 이번 task에 필요한 최소 역량만 활성화하고, 기존 프로젝트 Worker가 같은 역량을 충족하면 재사용한다.

## 목차

1. 공통 역량
2. 조건부 ERP 전문가
3. 기존 Worker 매칭
4. 생성 지침

## 1. 공통 역량

### project-mapper

- 기본 권한: read-only
- 목적: 프로젝트 규칙, stack, module boundary, 실행·검증 명령, 위험 영역을 빠르게 지도화한다.
- 기존 후보: `explore`, `explorer`, `pm`, `project-analyst`, `code-mapper`
- 산출물: 관련 파일 지도, 규칙 출처, 변경 후보, 불확실성

### erp-domain-analyst

- 기본 권한: read-only
- 목적: as-is/to-be 업무 흐름과 수량·금액·상태·권한·대사 불변조건을 수용 기준으로 바꾼다.
- 기존 후보: ERP 규칙을 명시적으로 읽는 `pm`, `business-analyst`, `domain-reviewer`
- 필수 관점:
  - 품목수와 총수량 구분
  - 가격 유효성 및 fail-closed 선택
  - 주문→반품/교환→전표 수량 승계
  - 누적 수량과 동시성
  - 조직·역할별 데이터 격리
  - 외부 원본, 내부 정본, 재처리 경계

### implementation-worker

- 기본 권한: write
- 목적: Lead가 지정한 파일/모듈 범위 안에서 가장 작은 구현을 수행한다.
- 기존 후보: `developer`, `executor`, `worker`, `backend-developer`, `frontend-developer`
- 규칙: architecture 결정을 임의 확장하지 않고, 범위 밖 리팩터링과 migration 적용을 하지 않는다.

### test-engineer

- 기본 권한: write
- 목적: 수용 기준과 ERP 불변조건을 unit/integration/E2E/DB test로 증명한다.
- 기존 후보: `tester`, `test-engineer`, `qa-tester`
- 필수 관점: happy/error/edge, 역할별 권한, 조직 격리, 중복 요청, 경계 수량, 재실행 가능성

### reviewer

- 기본 권한: read-only
- 목적: 구현에 참여하지 않은 관점에서 raw diff와 증거를 검토하고 PASS/FAIL을 판정한다.
- 기존 후보: `reviewer`, `code-reviewer`, `domain-reviewer`
- 금지: FAIL을 숨기기 위한 직접 수정

### verifier

- 기본 권한: read-only + 검증 명령
- 목적: Lead가 주장한 완료 조건을 fresh output으로 재측정한다.
- 기존 후보: `verifier`, `qa-tester`, `reviewer`
- 산출물: 명령, exit code, 핵심 결과, 미실행 사유

## 2. 조건부 ERP 전문가

### db-guardian

감지 신호: `supabase/`, `prisma/`, `migrations/`, PostgreSQL/MySQL/MSSQL dependency, RLS 문서.

- 기본 권한: read-only
- 목적: schema, FK, index, RLS, transaction, concurrency, migration compatibility를 검토한다.
- 기존 후보: `postgres-pro`, `db-migration`, `supabase-migrator`
- 실제 migration 적용은 하지 않는다. 필요하면 별도 write Worker가 승인된 migration 파일만 작성한다.

### ui-designer

감지 신호: React/Next/Vue/Flutter, design-system, UI kit, 화면·폼·대시보드 task.

- 기본 권한: read-only
- 목적: 고밀도 ERP 화면, DataTable/Tree/Master-Detail, 네 상태, 접근성, 반응형 계약을 설계·검토한다.
- 기존 후보: `designer`, `ux-auditor`, `frontend-designer`

### integration-specialist

감지 신호: Odoo, FM4/더존, OMS, marketplace/channel adapter, webhook, shipping, email.

- 기본 권한: read-only; 구현 task가 독립적이면 write
- 목적: 상태 매핑, idempotency, retry, rate limit, stale reconciliation, credential boundary를 검토한다.
- 기존 후보: channel/API/provider 이름을 가진 specialist

### security-auditor

감지 신호: auth, RLS, RBAC, organization scope, admin, PII, server mutation.

- 기본 권한: read-only
- 목적: 인증·인가 누락, 조직 간 노출, RLS 우회, service credential 노출, injection/XSS를 감사한다.
- 기존 후보: `security-auditor`, `security-reviewer`

### data-reconciler

감지 신호: Excel/import/export, legacy migration, collection, inventory/settlement reconcile, correction script.

- 기본 권한: read-only; dry-run script 작성 시 write
- 목적: source/transform/target count, missing/duplicate/mismatch, rollback, rerun safety를 검증한다.
- 실제 데이터 write는 별도 승인 전 금지한다.

### performance-auditor

감지 신호: high-volume table, batch/queue/cron, virtualized list, dashboard aggregate, slow query.

- 기본 권한: read-only
- 목적: N+1, missing index, unbounded fetch, full-memory load, rerender, external call volume을 측정한다.
- 기존 후보: `performance-engineer`, `performance-auditor`

## 3. 기존 Worker 매칭

이름만 같다고 재사용하지 않는다. 다음을 모두 확인한다.

1. description이 필요한 역량을 포함한다.
2. read/write 권한이 task와 맞는다.
3. project rules와 실제 stack을 읽도록 되어 있다.
4. 다른 ERP의 package manager, ORM, 외부 서비스가 하드코딩되지 않았다.
5. 산출물과 완료 조건이 Lead review에 충분하다.

충분하면 재사용하고, 일부만 부족하면:

- 기존 파일을 보존한다.
- 이번 prompt에서 누락 context를 보완할 수 있으면 파일 수정 없이 사용한다.
- 지속적인 수정이 필요하면 변경 diff와 이유를 사용자에게 제안한다.

## 4. 생성 지침

새 Worker instructions에는 다음을 포함한다.

- 특정 고객사나 절대경로 대신 현재 repo의 규칙·문서를 먼저 읽는 절차
- 역할 경계와 write 허용 여부
- ERP 관점의 필수 검증
- task scope 밖 변경 금지
- Lead에게 반환할 evidence 형식
- commit, migration apply, external write, push, deploy 승인 gate

Worker가 자체적으로 다른 Worker를 spawn하지 않게 한다. 분해와 dispatch는 Lead 한 곳에서만 소유한다.
