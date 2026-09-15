# 웹사이트 목적과 도구 선택

변경 모드와 별도로 페이지/구간의 목적을 고른다. 사용자 명시 선택과 프로젝트 계약을 보존하면서 [SKILL.md](../SKILL.md)의 `## 도구 기본값과 레거시 교체 정책`을 적용한다. 역할 분류는 현재 작업 범위에만 적용한다. 주 목적은 여섯 개이며 이 문서가 목적 목록과 라우팅의 소유 파일이다.

## 주 목적

| 사용자에게 필요한 결과 | 먼저 확정할 것 | 읽을 참조 | 기본 선택 방향 |
|---|---|---|---|
| 업무 UI: 등록·검색·수정·승인 | 핵심 과업, 정보 밀도, 입력/복구 흐름, 키보드 흐름, 권한별 상태 | [work-ui-surfaces.md](work-ui-surfaces.md), [web-quality.md](web-quality.md), [motion-design.md](motion-design.md); 표 안 차트는 [data-surfaces.md](data-surfaces.md) | 기존 UI와 Motion으로 명확한 상태·전환; 표·폼·필터는 work-ui-surfaces 기준 |
| 커머스: 탐색·비교·구매 | 상품 선택과 구매 완료 흐름, 브랜드 | [web-quality.md](web-quality.md), [motion-design.md](motion-design.md) | 탐색·옵션은 자연스럽게, 결제는 빠르고 명확하게 |
| B2C: 콘텐츠·참여·예약·가입 | 읽기·참여 또는 신청의 대표 행동 | [web-quality.md](web-quality.md), [motion-design.md](motion-design.md) | 콘텐츠 전환·참여 피드백과 처리 상태를 구분 |
| 데이터 대시보드: 비교·추세·이상 탐지 | 지표 정의, 기간, 비교 기준, 다음 행동, 레거시 차트 엔진 유무 | [data-surfaces.md](data-surfaces.md), [motion-design.md](motion-design.md); 대시보드 안 표·필터는 [work-ui-surfaces.md](work-ui-surfaces.md) | Bklit UI와 같은 데이터 동작 시안 세 개; 레거시 엔진은 교체 대상 |
| 홍보·콘텐츠: 이해·신뢰·신청 | 독자, 핵심 메시지, 증거, CTA, 검색/공유 | [web-quality.md](web-quality.md), [motion-design.md](motion-design.md) | HTML 읽기 흐름과 목적에 맞는 연출 |
| 그래픽·3D 체험: 제품/구조 설명·브랜드 영상·공간·놀이 | 전달할 내용, 관람/직접 조작, 정확도, 필요한 입력과 결과 | [graphics-production.md](graphics-production.md); 모델 필요 시 [ai-assisted-3d.md](ai-assisted-3d.md); runtime·scroll·성능은 [motion-and-3d.md](motion-and-3d.md) | 영상·scroll media·2D/2.5D·실시간·게임형·혼합을 비교하고 AI가 제작부터 웹 전달까지 수행 |

커머스나 B2C 안에도 업무·콘텐츠·브랜드 구간이 있다. 사이트 이름만으로 같은 모션 강도를 적용하지 않는다. 보조 역할을 추가할 수 있으나 필요 없는 참조까지 전부 읽지 않는다. 단순 KPI 한 개 때문에 차트 엔진을 추가하지 않는다. 지도·편집기 등 표 밖의 요구는 기존 구성과 공식 자료를 조사하고 억지로 위 도구에 맞추지 않는다.

판정 예:
- ERP 매출 대시보드의 차트 → 주 목적 데이터 대시보드, 보조 업무 UI(필터바·상세 표).
- ERP 주문 목록에 탭 추가 → 주 목적 업무 UI. 탭 패널에 차트가 없으면 data-surfaces를 읽지 않는다.
- 커머스 랜딩의 3D 제품 hero + 아래 옵션 선택 구간 → hero는 그래픽·3D 체험, 옵션 구간은 커머스. 구간별로 다른 강도.

## 선택 순서

1. stack·버전·기존 의존성/소스·승인된 패턴을 확인한다. 사용자의 표현만으로 경험이 불명확하면 [intent-to-experience.md](intent-to-experience.md)로 도메인과 과업에 맞는 이름·느낌·보완 요청문을 먼저 제안한다. 명확하면 생략하며 별도 승인 게이트를 추가하지 않는다.
2. **레거시 엔진 인벤토리**를 확인한다. [project-audit.md](project-audit.md)의 정적 인벤토리로 차트 엔진(ECharts·Chart.js·ApexCharts·Highcharts·구 Recharts wrapper 등)·표 라이브러리·모션 라이브러리와 사용처 파일 수(공통 wrapper 포함)·화면(route) 수를 기록한다. 대상 구간에 레거시 차트 엔진이 있으면 이번 범위의 이관과 전체 이관 제안을 계획에 넣는다(절차·예외: [data-surfaces.md](data-surfaces.md) `## 레거시 차트 엔진 교체`). 인벤토리를 건너뛰고 차트를 수정하지 않는다.
3. 사용자의 핵심 행동과 보이는 반응을 정의한다. Motion, Anime.js, Bklit, Three.js/R3F의 SKILL.md 기본 규칙을 적용한다.
4. 기존 승인 패턴은 재사용하고 새 모션·차트·그래픽 표현은 해당 소유 참조의 **공식 예제 관찰 → 채택 표현 지정 → 동작 시안 세 개 → 결과 대조**로 선택한다. 비호환·필수 기능 부재·실측 성능 제약이면 주 대안과 근거를 제시하고 필요한 결정 하나만 받는다.
5. 외부 생성·편집·premium 기능은 [tool-capabilities.md](tool-capabilities.md)에서 서비스별 권한과 결과 전달까지 확인한다. 이용 가능한 포함 유료 기능은 활용하고 무료 서비스는 그 범위로 실행한다.
6. [tooling.md](tooling.md)에 따라 실제 대상 프로젝트에 필요한 도구만 준비하고 연결한다. framework를 임의 이관하지 않는다.
7. 선택 이유와 제약을 기존 DESIGN 또는 구현노트에 짧게 남긴다. 개인 계정 정보는 공유 정본에 넣지 않는다.

## 필요한 결정 기록

| 항목 | 기록 예 |
|---|---|
| 모드 / 주 목적 | small-feature / 데이터 대시보드 |
| 사용자가 할 일 | 기간을 바꾸고 매출 감소 채널을 찾는다 |
| 의도 보완 / 전달 방식 | 명확해 생략 / 제품 hero는 영상, 옵션은 직접 조작 |
| 레거시 인벤토리 / 이번 이관 범위 | echarts 사용처 파일 7(공통 wrapper 1) / 화면 5 → 부분 적용: 1/5 화면 이관, 나머지 제안 중(이번 범위 매출 대시보드 1 화면·차트 2개; 실제 레거시 잔존 사용처 4 / 기록된 예외 0 / 미처리 이관 대상 4) |
| 재사용 / 추가 도구 | 승인 Motion 패턴 / Bklit 신규 비교 |
| 선택 이유 / 제외 대안 | 기존 UI 계약 유지 / 필요한 차트 표현을 Bklit로 구현 |
| 확인할 상태 / 제약 | 0과 누락 구분, 느린 조회, 모바일 범례, 권한별 열 노출 |
| 증거 | 대상 route·대표 데이터·검증 결과·레거시 import 0건 |

이 표를 또 다른 필수 문서로 만들지 않는다. 기존 정본에 같은 정보가 있으면 링크한다.

## 소유 규칙: 목적·도구를 추가할 때

- 새 **주 목적**을 추가하면 다음 여덟 곳을 함께 고친다: (1) 이 파일의 `## 주 목적` 표, (2) [SKILL.md](../SKILL.md) `## 작업 분류`의 목적 목록, (3) [PRODUCT 템플릿](../assets/PRODUCT.template.md)의 `Primary website purpose`, (4) [gate 템플릿](../assets/design-gates.template.md)의 `Primary purpose and scope`, (5) [DESIGN 템플릿](../assets/DESIGN.template.md)의 `Primary purpose and affected routes/sections` 목적 열거, (6) 전용 참조, (7) [verification.md](verification.md)의 목적별 검증 항목, (8) [design-context.md](design-context.md)의 대응 필드·기록 기준·목적 열거·필드 개수.
- 새 **도구**를 추가하면 다음 일곱 곳을 함께 고친다: (1) [SKILL.md](../SKILL.md) 도구 선언 표, (2) [tooling.md](tooling.md) 설치 표, (3) 해당 목적 참조, (4) [DESIGN 템플릿](../assets/DESIGN.template.md)의 결정 필드, (5) [gate 템플릿](../assets/design-gates.template.md)의 `Relevant experience evidence` 행, (6) [verification.md](verification.md)의 검증 항목, (7) [design-context.md](design-context.md)의 대응 필드·기록 기준·목적 열거·필드 개수.
- 이 두 목록은 SKILL.md `## 규칙 소유`의 목록과 같은 항목·같은 순서다.
- 위 목록에 없는 파일(예: mode-selection·intent-to-experience·standalone-visuals·web-quality)은 새 목적·도구를 본문에 다시 정의하지 않고 소유 파일 링크로만 가리킨다; 그 파일이 이미 목적·도구 이름을 열거하고 있으면 열거만 같은 이름으로 갱신한다. 위 항목 중 하나라도 빠지면 추가를 완료로 보지 않는다.

## AI 제작 서비스의 위치

[Manus Webapp](https://www.manus.im/features/webapp)은 사이트를 생성하는 서비스이며 앱에 설치하는 UI 라이브러리가 아니다. 사용자가 외부 빌더를 원하거나 초기 시제품에 적합할 때만 선택한다. 기존 고객 앱을 자동 이관하지 않는다. [운영 과금](https://help.manus.im/en/articles/13885710-how-does-webdev-billing-work), 코드/데이터 내보내기와 실제 인증·배포 구조를 확인한다. 생성 결과도 같은 디자인 게이트와 구현 검증을 통과해야 한다.
