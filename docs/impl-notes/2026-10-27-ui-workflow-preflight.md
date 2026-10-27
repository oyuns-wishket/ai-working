# 2026-10-27 UI 사전 판정과 구조 시안 누락 방지

## 목표 / 확정 사항
- 기존 디자인 체계의 메뉴 재구성에서 디자인 스킬 적용·배치 시안이 누락되는 재발 경로를 줄인다.
- 스타일/컴포넌트 재사용과 정보 구조/배치/탐색 재사용을 분리한다. 브랜드 인터뷰를 불필요하게 재개하지 않는다.

## Gate evidence
- 사용자 요청: UI 작업 중 디자인 스킬·시안 누락이 반복되므로 SSOT의 UI workflow를 강화.
- 확인 질문: 없음. 반복 실패와 원하는 교정 범위가 명확하다.
- 승인된 범위: 전역 진입 규칙·design-workflow·dev-protocol·관련 템플릿과 인계의 로컬 수정 및 검증·설치 연결 확인.
- 후속 승인: 사용자가 “원격까지 다 반영하고 정리”를 요청하여 이번 UI workflow 변경의 commit/push·원격 CI 확인을 승인했다. 타 장비 적용은 요청하지 않았다. 제품 UI 구현 요청이 아니므로 화면 시안은 해당 없음.

## Issue tracking
- 생략: 재사용 지침의 제한된 교정이며 별도 이슈 생성·외부 write 없이 기존 실패를 이 노트에 연결한다.

## 사각지대 / 계획
- 호출자가 스킬을 읽지 않으면 본문 강화만으로 효과가 없다 → 전역 규칙과 dev-protocol 진입점도 수정.
- scoped N/A와 모션 재사용이 구조 시안까지 면제할 수 있다 → 독립 UX 판정·gate 행과 잠금 해제 조건을 연결.
- 단순 치환·이미 결정된 구조에도 재승인을 요구할 수 있다 → 비대상·기존 결정 재사용 분기를 명시하고 독립 시나리오 검토.
- 다른 세션의 staged 변경·설치 상태가 있다 → 기존 변경을 보존하고 bootstrap dry-run/status로 영향 확인.
- 계획: 관련 진입점·소유 규칙 수정 → 시나리오 검토·기존 검사 → bootstrap 및 양 에이전트 연결 확인.

## 변경 / 판단 근거
- 전역 규칙: UI 사전 판정을 계획 확정/application source 수정 앞으로 배치.
- dev-protocol: 명확한 기능 요구사항이 디자인 판정을 대체하지 않음을 명시.
- design-workflow: 메뉴·탭의 개수와 내부 구성을 구분하고, 변경 중 UI 범위가 추가되면 재판정. 같은 브랜드 안에서 변경 구간의 구조가 다른 세 시안으로 결정.
- gate template: UI structure and navigation 증거와 잠금 해제 항목 추가. 모드 판정·탭 예시도 연결.
- 대안: 키워드 기반 hook으로 모든 UI 파일 편집 차단은 채택하지 않음. 파일 경로·단어로 실제 UX 변경/기존 승인을 판정할 수 없어 오탐·형식적 marker 우회가 생긴다. 이번 변경은 지침과 기록 기준이며 OS 수준 강제 차단이 아니다.

## DEVIATION
- 개인 규칙 동기화 SSOT이며 기존 staged 변경이 있어 primary checkout에서 필요한 문서만 수정한다. 다른 세션의 파일·staged 변경은 보존한다. publication은 이번 UI 변경만 별도 index에서 구성해 commit하며, 공유 README/HANDOFF의 다른 작업 내용은 포함하지 않는다.
- 이 노트는 첫 문서 수정 직후 작성했다. 첫 write 전 기록 원칙을 충족했다고 소급 표시하지 않는다.

## 검증
- `python3 scripts/validate_skills.py`: 25개 스킬 통과.
- `python3 scripts/public_audit.py --history`: 공개 내용·전체 이력 검사 통과.
- `node --test tests/*.test.mjs`: 80개 통과, 실패/skip 0. hook·bootstrap 회귀 포함.
- `python3 -m unittest discover -s tests -p 'test_*.py'`: 90개 통과.
- `quick_validate.py skills/design-workflow`: 기본 Python에 PyYAML이 없어 첫 실행 실패. `uv run --with pyyaml python .../quick_validate.py skills/design-workflow`의 격리 의존성으로 재실행 통과. 시스템 Python 패키지는 변경하지 않음.
- `git diff --check`: 통과.
- 독립 read-only 시나리오 검토: 메뉴 내부 배치 미정 / 단순 라벨 치환 / 기존 그룹의 같은 배치 항목 추가 / 기존 구체적 배치 결정 / 구현 후 누락 발견의 다섯 경우를 구분. 정지 형식에도 UI 구조 행을 추가하고 기존 결정 재사용과 새 시안 소급 승인을 구분하도록 보완.
- `./bootstrap.sh --dry-run`, `./bootstrap.sh`, `./bootstrap.sh --status`: 변경 0, 정상 76, 문제 0. Claude/Codex의 실제 카탈로그 경로에서 design-workflow 전체 디렉토리가 같은 정본으로 resolve되고 사전 판정 내용이 보임을 확인. 처음 Codex 경로를 잘못 가정한 읽기 검사는 실패했으며, 현재 설치 경로로 정정해 확인했다.
- 후속 publication: 이번 UI 변경만 commit/push하고 해당 commit의 public-safety 성공을 확인한다. 다른 장비 동기화는 미적용. 새 세션에서 갱신된 description을 로드할 수 있음.

## 다음에 참고
- 같은 탭 컴포넌트·색·전환을 쓰더라도 콘텐츠 귀속·그룹·순서가 바뀌면 구조 재사용의 증거가 별도로 필요하다.
- 지침·링크 검사는 실제 장기 준수율을 증명하지 않는다. 후속 UI 작업에서 사전 판정 기록과 제시된 시안을 확인해야 한다.
