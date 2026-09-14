# Web-focused design workflow

## 목표 / 확정 사항

웹 개발에서 제품 목적에 맞는 표현과 도구를 선택하고, 정렬·가독성·응답성·접근성을 실제 증거로 평가한다. 기존 신규·리브랜딩 승인 게이트와 Claude/Codex 공용 정본을 보존한다.

## Gate evidence

- 요청: design-workflow를 웹 개발과 체감 품질에 맞게 개선.
- 승인된 범위: 스킬·참조·템플릿·보조 스크립트 개선, 검증, 로컬 공용 스킬 적용 및 해당 변경의 commit/push·배포.
- 확인 질문: 없음. 제품 화면을 만드는 작업이 아니므로 시각 방향·comp 선택은 해당 없음.
- 범위 밖: 유료 서비스 사용, 실제 고객 제품 구현·배포.
- 격리: 전용 branch/worktree에서 작성·검증 후 정본에 검증된 변경만 이관.

## 계획

1. 현재 실행 순서·설치 동작과 공식 기술 자료를 대조한다.
2. 변경 모드와 사이트 목적을 분리하고 해당하는 참조만 읽게 한다.
3. 웹 품질 기준·역할별 검증과 결정 기록을 보강한다.
4. audit 설치 차단, provider 설치 무결성을 회귀 테스트한다.
5. 스킬 검사·공개 저장소 검사·hook/bootstrap 테스트와 독립 시나리오 검토를 실행한다.

## 판단 근거

- 기존 stack·design system 우선. 도구 후보는 자동 설치 목록이 아니다.
- 모델 생성, 렌더링, 스크롤 제어를 분리한다.
- 만족도 점수는 만들어내지 않는다. 과업 완수와 측정 결과를 사용자 피드백과 구분한다.
- 기존 모드와 신규 디자인의 3방향·3시안 승인을 보존한다.

## 검증

- 설치 CLI 회귀 테스트 11개 통과: audit 불변성, dry-run 무변경, 설치 idempotency, provider 누락·빈 entrypoint·내용 차이 보존.
- 저장소 Python 17개(회귀 11개 포함), runtime guard 11개, knowns context 5개, publish 16개, multi-agent 5개, wiki context 15개 통과: 총 69개.
- Node hook/bootstrap 테스트 7개 통과.
- 스킬 validator 26개 통과, skill-creator quick validator 통과. quick validator의 YAML 의존성은 임시 uv 환경으로 제공했고 저장소 의존성을 추가하지 않았다.
- public audit의 현재 트리·전체 history 검사 통과. 문서의 일반 호스트명 예시가 검사에 걸려 실행 시 호스트명을 발견한다는 설명으로 바꿨다.
- git diff whitespace, shell syntax, JSON 구조 검사 통과.
- 독립 forward-test 6개: 기존 Vue 정렬, 신규 3D 분해 랜딩, 기존 Recharts 개선, 읽기 전용 audit, non-Git 덱, 모바일 모션 축소. 최종 잔여 blocker 없음.
- 이 저장소에는 앱 build/lint 명령이 없다. 위 syntax/metadata·자동 테스트로 검증했으며 실제 고객 UI의 사용자 만족도나 성능 개선을 실측한 것으로 주장하지 않는다.
- 설치 테스트는 임시 fixture와 mock CLI에서 수행했다. 외부 Taste/Impeccable의 새 버전 설치 검증은 이번 변경에 포함하지 않았다.

## 로컬 적용과 인계

- 검증된 18개 파일을 개인 동기화 저장소의 main 직접 반영 예외에 따라 로컬 정본으로 이관하고 byte 단위 일치를 확인했다. 게시 승인은 확보했으며 이 변경만 commit/push 대상으로 고정한다.
- 정본에서 bootstrap 실행: 변경 0개, 문제 0개, 정상 연결 69개. 기존 링크가 이미 정본을 가리켜 재연결이 필요하지 않았다.
- 게시 후 task 파일이 정본 커밋과 일치하는지 확인하고 작업 전용 worktree만 정리한다. 다른 작업의 worktree는 수정하거나 정리하지 않는다.
- 앱 배포 대상 없음. 운영배포 후 knowns 클로즈아웃은 해당 없음.

## ⚠️ DEVIATION

없음.
