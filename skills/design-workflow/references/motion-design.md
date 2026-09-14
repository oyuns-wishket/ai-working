# Motion과 Anime.js를 사용하는 웹 모션 설계

웹 UI 작업에서 모션 설계는 기본 항목이다. ERP·커머스·B2C라는 업종과 별도로 페이지의 과업과 브랜드 톤을 판단한다. 신규 상호작용에는 Motion을 기본으로 사용하고, 애니메이션·인터랙션 연출 요청에는 Anime.js를 준비해 해당 연출에 연결한다. 설치·재사용은 [tooling.md](tooling.md), 유료 예제는 [tool-capabilities.md](tool-capabilities.md)를 따른다.

## 과업별 추천

| 현재 과업 | AI가 추천할 동작 | 확인할 결과 |
|---|---|---|
| ERP·관리자 반복 처리 | 탭 이동, 행 펼침, 갱신 부분 강조, 저장 상태 연결 | 입력을 방해하지 않고 변경과 완료를 이해함 |
| 커머스 탐색·비교 | 상품 이미지·옵션 전환, 상세 진입, 필터·장바구니 반응 | 선택한 상품과 현재 위치를 유지함 |
| 결제·예약·가입 | 단계 진행, 오류 위치, 제출 중·실제 완료 피드백 | 중복 제출·입력 유실 없이 과업을 끝냄 |
| B2C 콘텐츠·커뮤니티 | 상세 확장, 저장·좋아요, 메뉴·피드 전환 | 읽기 흐름과 반응의 맥락을 유지함 |
| 브랜드·제품 소개 | 순차 등장, 장면 전환, 선택적 scroll story | 메시지와 CTA를 발견하고 이해함 |

같은 쇼핑몰에서도 히어로·상품 목록·결제는 다른 강도를 사용할 수 있다. 같은 과업에는 차분한 프리미엄·친근함·역동성 등 브랜드의 표현을 반영한다. 업종을 이유로 전체 화면을 정적 또는 화려한 모션으로 고정하지 않는다.

버튼/카드의 press·선택, 탭 표시와 패널, 목록/테이블 변경, 모달/드로어, 폼의 loading/error/success 중 해당하는 동작을 계획에 포함한다. 큰 목록의 긴 순차 등장, 반복 업무를 기다리게 하는 연출은 선택 이유가 있어야 한다. 결제·예약 성공은 실제 응답 이후 표시한다.

## 모션을 모르는 사용자와 선택하기

1. 기존 답변·디자인·대표 과업에서 원하는 느낌을 파악한다. 추가 결정이 필요하면 “빠르고 차분하게 / 부드럽게 이어지게 / 브랜드가 드러나게”처럼 묻는다. easing·spring 수치를 사용자에게 결정시키지 않는다.
2. AI가 한 방향과 이유를 추천한다. 예: “상품 탐색은 부드럽게 연결하고 결제는 짧게 반응하도록 추천합니다.”
3. 새로운 모션 방향은 **같은 콘텐츠와 대표 행동으로 동작 시안 세 개**를 함께 보여준다. 기본 축은 빠른 반응·부드러운 연결·브랜드 표현이며 프로젝트에 맞게 구성한다. 정지 이미지나 외부 예제 링크만 제시하지 않는다.
4. 재생·초기화와 직접 클릭/스크롤을 제공한다. 신규 디자인에서는 기존 composition 세 시안 안에 통합한다. 기존 디자인에서는 해당 컴포넌트/흐름만 비교한다.
5. “B인데 더 빠르게”, “카드는 B, 결제는 A” 같은 실제 답을 토큰·패턴으로 바꾸고 채택·수정 근거를 기록한다. 사용자가 모르면 먼저 체험할 수 있게 하며 임의로 취향을 확정하지 않는다.

이미 승인된 패턴을 작은 변경에서 재사용할 때는 재선택을 요구하지 않는다. 새 표현이 필요한 경우만 비교한다. 사용자가 시안을 본 뒤 AI에게 선택을 위임하면 그 범위에서 결정한다. 시안과 구현은 main skill의 잠금·승인 경계를 유지한다.

## 구현 계약

| 대상 | 기본 담당 | 적용 방식 |
|---|---|---|
| UI 상태·layout·gesture | Motion | 설치된 stack의 API, layout/공유 요소/등장·퇴장 패턴 |
| 요청된 SVG·순차 연출·복합 timeline | Anime.js | 컴포넌트 scope, timeline, cleanup까지 실제 연결 |
| 3D scroll scene | [motion-and-3d.md](motion-and-3d.md) | 진행률·카메라·모델 속성의 소유자를 하나로 지정 |

Anime.js 연출 요청이 오면 설치 여부만 확인하고 끝내지 않는다. 기존 API로 해당 연출을 구현하거나 없는 경우 로컬 설치한다. 두 도구를 쓰면 예를 들어 Anime.js는 hero timeline, Motion은 메뉴·카드의 상태를 맡긴다. 동일 속성에 두 엔진을 연결하지 않는다. 사용자 요청 전체가 기존 승인 Motion 패턴 재사용이면 불필요한 Anime.js 의존성을 추가하지 않는다.

React에서는 기존 `framer-motion`/`motion` 버전·import·공통 wrapper를 먼저 확인한다. 호환되는 기존 구성을 사용하고 두 패키지를 중복 추가하거나 요청 없이 major upgrade하지 않는다. 기존 semantic markup·폼 상태·focus·가상화 계약을 유지한다. 비React에서는 공식 해당 stack 경로를 확인하고 불가능한 API를 복사하지 않는다.

DESIGN 정본에 페이지별 강도와 timing/easing/distance/spring, 반복·연속 입력 정책, reduced motion, 엔진별 대상, 선택한 시안과 재사용 범위를 남긴다. 코드의 기존 토큰/패턴 저장 위치를 사용하며 모든 프로젝트에 같은 wrapper 구조를 강제하지 않는다.

## 무료·유료

Motion 코어의 무료 기능으로 기본 상태·layout·scroll을 구현할 수 있다. Motion+의 접근 권한이 있으면 선택한 예제·프리미엄 기능을 활용하되, 팀/사용 범위와 실제 접근을 확인한다. 유료 계정이 없으면 무료 예제·코어 구현을 사용한다. 유료 소스의 접근 제한을 우회하지 않는다. 전용 Three.js 통합 같은 별도 premium/early-access API를 무료 안정 기능으로 가정하지 않는다. 플랜·가격은 스킬에 고정하지 않는다.

## 실제 확인

- 선택한 대표 과업을 mouse/touch/keyboard로 실행하고 연속 입력 시 자연스럽게 이어지는지 확인한다.
- focus, disabled, loading, 오류 복구와 기존 데이터·결제 계약을 보존한다.
- OS reduced motion을 Motion 설정과 커스텀 JS·3D·영상에 반영한다. 모바일은 hover 없이 중요한 기능을 조작할 수 있어야 한다.
- unmount·route 재진입 시 timeline/listener 중복을 확인한다. 실제 성능은 기기·조건을 기록해 측정한다.
- 사용자가 승인한 인상과 실제 결과를 비교한다. 설치 성공이나 정지 캡처만으로 움직임 검증을 대신하지 않는다.

공식 근거: [Motion](https://motion.dev/docs/react), [layout](https://motion.dev/docs/react-layout-animations), [accessibility](https://motion.dev/docs/react-accessibility), [Motion+](https://motion.dev/plus), [Anime.js 설치](https://animejs.com/documentation/getting-started/installation/), [React scope/cleanup](https://animejs.com/documentation/getting-started/using-with-react/).
