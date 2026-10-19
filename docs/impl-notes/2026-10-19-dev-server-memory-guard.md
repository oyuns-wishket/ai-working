# 2026-10-19 dev server 메모리 누적 재발 방지

## 목표 / 확정 사항

- 여러 화면을 순회하는 audit·E2E·캡처를 dev server(`next dev`·`vite` 등)에서 돌리다 메모리가 계속 커지는 일을 막는다.
- 다른 세션의 dev server가 메모리를 압박할 때 agent가 무엇을 해야 하는지(자기 것은 정리, 남의 것은 보고)를 매 세션 규칙과 resource guard 알림으로 준다.

## Gate evidence

- 사용자 요청·답변(2026-10-19): swap 원인 조사 결과를 보고 "2 즉시 회수 해줘" → 3217 dev server 종료. 이어서 "ㅇㅇ 그렇게 하고 그런 개선을 dev protocol 스킬 혹은 global ssot인 ai-working의 적절한 CLAUDE.md나 AGNETS.md에 넣어서 매번 적용되게 해줘".
- 확인 질문: 없음. 반영 위치(전역 규칙·dev-protocol)는 사용자가 지정했고, hook 알림 보강은 같은 목적의 가역적 구현 선택으로 판단했다.
- 승인된 범위: `global/CLAUDE.md`, `skills/dev-protocol/`, `hooks/dev-resource-guard.mjs`와 테스트, `docs/hook-behavior.md`, 이 노트, README 이력 링크. 개인 동기화 저장소라 main 직접 commit·push, 이 장비의 설치 반영(bootstrap)까지.
- 미승인 가정: 다른 세션의 dev server를 hook이 자동 종료하지 않는다. 다른 세션 branch의 미커밋 작업은 건드리지 않는다.

## Issue tracking

- 대표: 생략 — 개인 SSOT 저장소의 규칙·hook 보강이고 관련 열린 이슈가 없다(`gh issue list` 0건).
- 완료 시점: main 반영 + 이 장비의 설치 경로에서 규칙·hook 반영 확인.

## 사건 (실측, 2026-10-19)

- 48GB Mac에서 swap 32.4/33.8GB 사용. `top -o mem` 기준 한 Next 16 dev server(`next-server`)가 MEM 75GB(그중 압축 70GB)였다.
  같은 시점 `ps` RSS는 5.7~6.2GB로 보여 실제 사용량을 크게 과소 표시했다.
- 그 서버는 다른 Claude 세션이 띄웠고, 그 세션의 audit 스크립트가 Playwright로 여러 route를 순회하는 중이었다. 5초 간격 측정에서 RSS가 계속 늘고 CPU는 약 150%였다.
- 사용자 승인 후 프로세스 트리(npm → next → next-server → worker)에 TERM을 보내 종료했다. swap 11.7GB, 여유 메모리 35% → 77%로 회복.
- 같은 시점 resource guard는 `RESOURCE_PRESSURE`를 냈지만, 안내가 Supabase stack 정리뿐이라 이 상황에서 할 행동이 없었다.
- 원인 추정(미확인): dev 모드는 처음 여는 route를 그때 컴파일하고 결과를 메모리에 남긴다. 그래서 화면을 많이 순회하면 계속 커진다. 누수인지 특정 route 때문인지는 확인하지 않았다.

## 계획

1. 전역 규칙에 한 줄 추가: dev server 소유·종료, 여러 화면 순회는 production build 서버, 소유 불명 서버는 보고.
2. `dev-protocol/references/local-operations.md`에 dev server 절 추가(측정 방법, 압박 시 처리, 승인 후 종료 절차). SKILL.md와 전역 규칙의 "언제 읽나" 조건에 dev server를 넣는다.
3. resource guard: 메모리 압박일 때만 dev server 후보를 `footprint`로 재고, 4GB 이상을 PID·용량·cwd로 알린다. 압박 안내 문구에 dev server를 넣는다.
4. 검증: `node --test tests/*.test.mjs`, `python3 scripts/validate_skills.py`, `python3 scripts/public_audit.py --history`, 실제 장비에서 hook 실행.

## 판단 근거

- 규칙만으로는 부족하다: 이번 세션도 규칙상 "소유권 불명 자원은 끄지 않는다"를 지켰지만 75GB까지 아무도 알아채지 못했다. 매 턴 들어가는 hook 알림에 원인 프로세스를 보여야 행동으로 이어진다.
- 압박일 때만 잰다: 평소에는 probe 비용과 소음이 0이다. 이번처럼 swap이 찬 상황에서만 필요한 정보다.
- `ps` RSS 대신 `footprint`: 압축·swap된 메모리를 포함한다(이번에 RSS 6GB 대 실제 75GB). `--pid`를 명시한다. 위치 인자는 프로세스 이름으로도 해석되어 엉뚱한 프로세스가 잡혔다(`1` → 1Password 계열).
- 자동 종료는 기각: 다른 세션의 작업(진행 중 audit·로그인 상태)을 깨므로 사용자 결정이 필요하다. hook은 정보만 준다.
- 4GB 기준: 정상 Next dev server는 1~3GB였고, 문제 서버는 수십 GB까지 갔다. 16GB 장비에서도 의미 있는 크기다.
- Linux·`footprint` 부재 환경에서는 조용히 생략한다. CI(ubuntu)는 fake로 검증한다.

## ⚠️ DEVIATION

- 없음

## 다음에 참고

- `RESOURCE_PRESSURE`는 swap ≥ 8GB면 계속 켜진다. macOS swap은 여유가 생겨도 천천히 줄어서, 회복 뒤에도 한동안 경고가 남는다. 필요하면 free%와 함께 판단하도록 기준을 조정할 후보다.
- cross-session 메시지는 받는 세션의 permission mode가 다르면 보류됐다가 만료된다. 다른 세션에 알릴 내용은 사용자에게도 같이 보고한다.
