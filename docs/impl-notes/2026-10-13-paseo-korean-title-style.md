# Paseo 자동 제목을 한국어 짧은 이름으로 (2026-10-13)

## 목표와 요청
Paseo 사이드바의 워크스페이스 제목이 영어 문장으로 길게 생성되어 잘린다. 사용자가 "작업할 때 깔끔하게 10자 이내
제목이 달리게" 수정을 요청했다.

## 확인한 사실 (Paseo desktop 0.11.2 번들 코드 기준)
- 제목은 첫 프롬프트로 내부 구조화 생성 agent가 만들고, 기본 지시문은 영어 "약 4단어, 최대 80자"다.
- 바꿀 수 있는 곳은 repo 루트 `paseo.json`의 `metadataGeneration.title.instructions` 하나다. 데몬 전역 설정의
  `agents.metadataGeneration`은 생성에 쓸 provider만 받는다.
- 지시문은 커밋 여부와 무관하게 디스크의 파일에서 읽는다. Paseo가 만든 worktree는 원본 repo 루트, 그 외
  checkout은 자기 루트를 본다. Git repo가 아닌 폴더는 기본 지시문으로 떨어진다.

## 변경
- `paseo.json`: 이 저장소의 제목 지시문 추가.
- `skills/paseo-setup/scripts/title_style.py`: 지시문 정본과 적용 스크립트. 미추적 repo는 `paseo.json`을 만들고
  `.git/info/exclude`에 등록해 Git에 흔적을 남기지 않는다. 추적 중인 파일은 `--tracked`를 줘야 작업 트리를 고친다.
- `skills/paseo-setup/SKILL.md`: 고정값 표와 2-1절에 제목 스타일 절차 추가.

## 근거와 기각한 대안
- 제목 언어는 개인 취향이라 팀 repo에 커밋하면 팀원 화면도 바뀐다. 그래서 로컬 전용을 기본으로 했다.
- 전역 규칙(`global/CLAUDE.md`)에 넣는 안: 생성 agent가 규칙 파일을 읽는지 보장되지 않아 기각.
- 앱 번들 패치: 업데이트마다 사라지고 서명을 깨므로 기각.
- 추적 파일에 `skip-worktree`를 거는 안: upstream 변경 시 checkout이 막혀 다른 세션을 방해하므로 기각.

## 검증
- 임시 repo 3종(미추적·추적·비Git)에서 `LOCAL`/`TRACKED`/`SKIP` 분기와 재실행 멱등성, `git status` 무변화 확인.
- 번들의 `buildMetadataPrompt`를 직접 호출해 지시문이 "Title style" 블록을 대체하는 것과, `paseo.json`이 없는
  폴더에서는 기본값이 쓰이는 것을 확인.
- 같은 프롬프트를 haiku에 4건 실행: 8·9·11·10자의 한국어 제목이 나왔다. 초과 1건을 보고 "10자를 넘으면 단어를
  줄인다"를 추가했다. 글자 수는 모델 준수에 달려 있어 강제되지 않는다.
- 실제 Paseo UI에서 새 워크스페이스를 만들어 확인하는 검증은 하지 않았다.

## 남은 일
- 추적 중인 `paseo.json`을 가진 팀 repo는 커밋 여부를 사용자가 정한 뒤 적용한다.
- Paseo가 전역 지시문 설정을 제공하면 repo별 적용을 걷어낸다.
