# Portable checkout path

## 요구사항
- 새 사용자의 환경에 원작성자의 `dev-oh` 폴더가 생성되지 않아야 한다.
- 저장소·폴더 이름과 실제 위치는 개인화 인터뷰에서 사용자에게 먼저 받아야 한다.
- 설치된 hook과 이후 SSOT 수정은 사용자가 선택한 public ai-working checkout을 찾아야 한다.

## 원인
- README quick-start가 원작성자의 로컬 경로를 기본값으로 복사했다.
- 복사 설치되는 `session-context.sh`도 같은 경로를 fallback으로 사용했다.

## 구현
- README는 저장 위치 선결정과 중립적인 `~/ai-working` 예시를 사용한다.
- personal-ai-ssot는 위치 답변 전 clone·mkdir·bootstrap을 금지한다.
- session-context hook은 환경변수 또는 설치된 Codex/Claude symlink에서 checkout root를 해석한다.
- 임의의 공백·한글 checkout에서 root를 찾고 `dev-oh`를 만들지 않는 회귀 테스트를 추가한다.
- 공개 감사기는 원작성자 checkout 이름이 현재 실행 tree에 재등장하면 실패한다. 이미 배포된 commit history는 실행 경로가 아니며 기존 clone을 깨뜨리는 history rewrite를 피하기 위해 이 항목의 history 검사에서는 제외한다.
- PR 검증 중 gitleaks action의 최신 요구사항에 맞춰 pull request scan에 `GITHUB_TOKEN`을 명시했다.

## 추적
- https://github.com/oyuns-wishket/ai-working/issues/2
