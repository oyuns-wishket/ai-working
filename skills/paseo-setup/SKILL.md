---
name: paseo-setup
description: Use when setting up Paseo worktree config for a repo — 레포를 분석해 스택에 맞는 paseo.json을 생성하고 기본 브랜치에 커밋한다. Triggers on "paseo 세팅", "paseo-setup", "paseo.json 만들어", "워크트리 세팅", "worktree config", "이 레포도 paseo", "paseo worktree setup". 분석·생성·커밋은 AI가 직접, 사용자는 방침 결정만.
---

# paseo-setup — 레포 분석 기반 paseo.json 생성·커밋

## Overview
Paseo(https://paseo.sh)는 git worktree로 병렬 에이전트 작업공간을 격리하는 도구다. 워크트리는 의존성·untracked 파일(`.env` 등) 없이 맨몸으로 생성되므로, 레포 루트에 `paseo.json`(setup 훅 + 서비스 정의)을 **기본 브랜치에 커밋**해 둬야 자동 세팅이 발동한다. 이 스킬은 임의 레포를 분석해 스택에 맞는 `paseo.json`을 생성하고 커밋까지 처리한다. 고정 템플릿 복붙이 아니라 **분석 → 맞춤 생성**이 본체다.

## 고정값 (정본)
| 항목 | 값 |
|---|---|
| 공식 문서 | https://paseo.sh/docs/worktrees |
| 워크트리 저장 위치(기본) | `~/.paseo/worktrees/<소스경로 해시>/<슬러그>/` |
| 전역 설정 | `~/.paseo/config.json` (`worktrees.root`, `servicePorts`만 — 전역 setup 훅은 **없음**, 레포별 paseo.json 필수) |
| paseo.json 읽는 위치 | **기본 브랜치에 커밋된 버전만** (untracked/타 브랜치 무효) |
| 기본 브랜치 | 추측하지 않고 `git remote show origin \| grep HEAD`와 프로젝트 규칙으로 확인 |
| 원본 레포 참조 변수 | `$PASEO_SOURCE_CHECKOUT_PATH` (setup에서 env 복사용) |
| 서비스 포트 변수 | `$PASEO_PORT` (워크트리별 동적 할당 — 하드코딩 금지) |
| 프록시 URL 형식 | `http://<script>--<branch>--<project>.localhost:<데몬포트>` |
| 워크스페이스 생성 | `paseo workspace create --isolation worktree --mode branch-off --new-branch <br> --base <기본브랜치>` (PR 재현: `--mode checkout-pr --pr-number N`) |
| 기존 설정 | 유효한 `paseo.json`이 이미 있으면 덮어쓰지 않고 필요한 차이만 갱신 |

## 절차

### 1. 레포 분석 (7항목 — 추측 금지, 전부 파일로 확인)
1. **패키지매니저/런타임**: lockfile(`package-lock.json`/`pnpm-lock.yaml`/`yarn.lock`), `packageManager` 필드, `requirements*.txt`/`pyproject.toml`, `pubspec.yaml`, `composer.json` → 설치 명령 결정 (`npm ci` / `pnpm install --frozen-lockfile` / `python3 -m venv .venv && .venv/bin/pip install -r ...`)
2. **env 방식**: `.env*` 파일 목록과 env bootstrap/sync 스크립트의 실제 구현을 확인한다. 고객 소유가 아니거나 현재 프로젝트에서 접근할 수 없는 credential source는 호출하지 않는다. 모노레포면 `scripts/lib.mjs`류의 `envFiles` 배열에서 앱별 경로 확인 → setup에서 `cp "$PASEO_SOURCE_CHECKOUT_PATH/<경로>" <경로>`로 복사한다.
3. **모노레포 여부**: `turbo.json`/`workspaces`/`pnpm-workspace.yaml` → 앱별 서비스 분리
4. **dev 서버·포트**: `scripts.dev` 파싱. **하드코딩 포트(`--port 3001` 등)는 우회**하고 `cd apps/<x> && npx next dev --port $PASEO_PORT`처럼 직접 바인딩
5. **검증 명령**: test/lint/typecheck 있는 것만 `scripts`에 등록
6. **특이 절차**: dev 전 사전 스크립트(폰트 복사 등), codegen, 마이그레이션 — dev 스크립트 원문에서 발견해 서비스 command에 포함
7. **teardown 필요 여부**: 워크트리별 로컬 DB 등 정리 대상 있을 때만 (보통 불필요)

### 2. paseo.json 생성
- `worktree.setup`: 명령어 **배열**로 (설치 → env 복사 순)
- `scripts`: 일반 스크립트는 `{ "command": ... }`, dev 서버는 `{ "type": "service", "command": "... --port $PASEO_PORT" }` — `port` 필드는 생략(자동 할당)
- 검증: `python3 -m json.tool paseo.json`

### 3. 기본 브랜치 커밋 (작업 체크아웃이 dirty여도 안전한 방법)
현재 체크아웃 브랜치·dirty 상태를 건드리지 않도록 **임시 worktree에서 1파일만 커밋**한다:
```bash
git fetch origin <기본브랜치>
git worktree add /tmp/paseo-<repo> -b feat/paseo-worktree-config origin/<기본브랜치>
cp paseo.json /tmp/paseo-<repo>/ && git -C /tmp/paseo-<repo> add paseo.json
git -C /tmp/paseo-<repo> commit -m "chore: Paseo 워크트리 설정(paseo.json) 추가" && git -C /tmp/paseo-<repo> push -u origin feat/paseo-worktree-config
gh pr create --base <기본브랜치> ... && gh pr merge --merge --delete-branch   # 커밋·머지 전 사용자 확인
git worktree remove /tmp/paseo-<repo> --force && git branch -D feat/paseo-worktree-config
```

## 검증 게이트
- [ ] `python3 -m json.tool paseo.json` 통과
- [ ] 기본 브랜치에 머지 완료 (`gh pr view --json state`)
- [ ] (권장) `paseo workspace create --isolation worktree --mode branch-off --new-branch test/paseo-smoke --base <기본브랜치>`로 setup 훅 발동 확인 후 archive

## 종료 지식화

Paseo 설정 생성·검증만으로는 `knowns`를 실행하지 않는다. 같은 작업 범위에 실제 제품 운영 배포가 포함되고 그 배포가 검증된 경우에만 최신 `dev-protocol`에 따라 `knowns`를 정확히 한 번 실행한다.

- 분석한 stack과 setup 사실, 선택 근거, smoke 결과, 실패 mode를 durable 후보로 삼되 env 값과 코드 원문은 제외한다.
- 사용자가 이 설정의 의미·목표·기여·성공 상태와 기존 운영/runbook 연결을 확인하고 exact write plan을 승인한 뒤에만 연결된 wiki를 갱신한다.
- 이미 `KNOWNS:` 결과가 있으면 재호출하지 않는다. 연결 wiki 없음/no delta/missing/blocked 결과를 완료 보고에 명시한다.

## 스택별 검증 패턴
| 스택 | setup | 서비스 |
|---|---|---|---|
| Next.js | lockfile에 맞는 install + 프로젝트 문서가 허용한 env 준비 | web dev server |
| turbo 모노레포 | 루트 install + 필요한 앱별 env 준비 | 각 앱을 독립 서비스로 선언 |
| Python | venv + 실제 `requirements*.txt` 전체 검토 | 서비스가 없으면 test/import check만 |
| 정적 HTML | 없음 | `$PASEO_PORT`를 사용하는 local HTTP server |

## 트러블슈팅
| 증상 | 원인 | 대응 |
|---|---|---|
| setup 훅이 안 돈다 | paseo.json이 기본 브랜치에 미커밋 | 기본 브랜치 머지 확인 (`git remote show origin \| grep HEAD`) |
| 워크트리 2개째 dev 서버 포트 충돌 | dev 스크립트에 포트 하드코딩 | 서비스 command에서 `$PASEO_PORT` 직접 바인딩으로 우회 |
| `gh pr merge --merge` 실패 | 레포가 merge commit 금지 | `--squash` → 그것도 막히면 `--rebase` 순으로 폴백 |
| env 복사 실패로 setup 중단 | 원본에 `.env.local` 없음(신규 클론) | `cp ... \|\| cp .env.local.example .env.local` 폴백. example도 없으면 고객 소유 provisioning 경로를 확인하고 blocker로 보고 |
| 작업 트리 dirty라 브랜치 전환 불가 | 기존 체크아웃에서 직접 브랜치 시도 | 절차 3의 임시 worktree 방식 사용 |
| Python 레포에서 test는 되는데 특정 모듈 ModuleNotFoundError | README만 믿고 requirements 일부만 설치 | `requirements*.txt` 전 파일을 검토해 setup에 포함하고 pytest 전체 수집 확인 |
| `paseo workspace` unknown command | CLI 구버전(0.1.x) — workspace는 0.2.x부터 | `npm i -g @getpaseo/cli@latest` (brew 아님 — npm 글로벌 설치본) |
