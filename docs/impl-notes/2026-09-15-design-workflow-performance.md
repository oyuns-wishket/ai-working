# 2026-09-15 design-workflow 성능 우선 개선

## 목표 / 확정 사항
- 사용자 결정: 효율이 아니라 **성능** 기준. 반복·중복이 있어도 결과 품질·승인 정확도·검증 강도를 최대화한다. `small-feature`도 범위만 좁고 강도는 전부.
- 사용자 결정: 차트는 Bklit로 통일하고 기존 ECharts 등 레거시 엔진은 교체 대상이다. 낮은 수준의 게이트 옵션은 만들지 않는다.
- 방법: 10점 루브릭(8항목)으로 독립 리뷰어(Claude Fable + Codex gpt-6-astra) 교차 채점, 평균 ≥ 9.5·항목별 ≥ 9.0까지 작성→채점→수정 반복.
- 루브릭·불변조건·시나리오: `/tmp/design-workflow-perf/rubric.md` (세션 작업 파일, repo 밖).

## Gate evidence
- 사용자 요청·답변: 분석 결과에 대해 1·4·5번 지적을 기각하고 "성능 관점으로 전체 맥락·기능·성능 흐트러뜨리지 않는 선에서 개선, 10점 만점 9.5 도달까지, 병렬 서브에이전트·다중 모델(fable, codex astra) 팀, 교차 검증 반복, ㄱㄱ".
- 확인 질문: 없음. 범위와 방법이 요청에 구체화됨.
- 승인된 범위: `skills/design-workflow/**` 편집(worktree `mad/design-perf/lead`), 검증 실행. commit/push는 개인 SSOT의 기존 승인 범위를 따르되 이번 대화에서 publication 승인은 명시되지 않음 → 완료 시 한 번 확인.
- 미승인 가정: 다른 스킬 본문 수정 없음(링크 갱신만), 외부 도구 설치 없음, 플러그인 사본 동기화는 별도 보고.

## Issue tracking
- 대표: oyuns-wishket/ai-working#13
- 관련: #12 (직전 그래픽·의도 확장, 완료)
- 완료 시점: 루브릭 통과 + validator/audit 통과 + commit/push(승인 시)

## 계획
1. 기준선 채점: 리뷰어 2명이 HEAD(main checkout, read-only)를 루브릭으로 채점.
2. Round 1 작성(병렬, 파일 소유권 분리):
   - L1 core (Fable): SKILL.md, mode-selection, experience-routing, design-context, project-audit, intent-to-experience
   - L2 data-erp (Fable): data-surfaces, web-quality, 신규 work-ui-surfaces.md
   - L3 motion-graphics (Codex astra): motion-design, motion-and-3d, graphics-production, ai-assisted-3d, tool-capabilities
   - L4 verify-assets (Codex astra): verification, feedback-improvement, tooling, standalone-visuals, assets/*
3. Lead 통합 검토(diff, 링크, 불변조건) → 리뷰어 2명 채점 → 결함을 lane에 배정 → 반복.
4. 종료 조건 충족 시 validate_skills / public_audit / 링크 검사 / 테스트 실행.

## 판단 근거
- multi-agent-dev의 "쓰기 Worker별 worktree" 대신 **lead worktree 하나 + 엄격한 파일 소유권 분리**를 택했다. 이유: 4 lane이 서로의 최신 텍스트를 읽어야 링크·용어 일관성(D2·D8)을 맞출 수 있고, 소유권이 겹치지 않아 충돌이 없다.
- Codex worker는 `codex exec -m gpt-6-astra -s workspace-write`로 native 호출한다. cliproxy 경유 확인됨.
- 리뷰어는 lane이 아니라 **스킬 전체**를 채점한다. 결함 배정은 Lead가 한다.

## ⚠️ DEVIATION
- ⚠️ 쓰기 Worker별 개별 worktree 미사용 → 대응: 파일 소유권 표로 충돌 차단, Lead가 매 라운드 `git status`/diff로 소유권 위반 검사 → 리뷰: 자체 확인

## 점수 진행 (평균 / D1..D8)
| 라운드 | Claude Fable | Codex astra | 비고 |
|---|---|---|---|
| baseline (HEAD 8d9d25a) | 6.75 (7/7/8/5/5/7/8/7) | 7.125 (7/7/8/6/5/7/10/7) | 결함 24 + 12 |
| round-1 | 8.625 (8/8/9/8/10/9/9/8) | 8.0 (7/7/8/8/10/7/10/7) | 기준선 결함 36건 전부 해소, 신규 20 + 6 |
| round-2 | 8.75 (8/8/9/8/10/9/9/9) | 8.25 (7/7/8/7/10/10/10/7) | r1 결함 26건 전부 해소, 신규 11 + 6. 리뷰어 충돌 3건은 Lead 결정으로 단일화 |
| round-3 FINAL | **9.25** (10/8/9/8/10/10/10/9) | **8.5** (10/7/10/7/10/10/10/7) | r2 결함 17건 전부 해소. 잔여 9건(모순 4·모호 2·표현 3, 전부 레거시 집계·대안 표 문구)은 Lead가 직접 수정, 재채점 없음(사용자 지시로 라운드 종료) |

## 종료 상태
- 목표(평균 9.5·항목 9.0) 미달 상태에서 사용자 지시로 종료. 최종 채점 후 Lead 수정분은 재채점되지 않았다.
- 검증: validate_skills 24 통과, public_audit 통과, diff-check 통과, 내부 링크·앵커 깨짐 0. 변경 21파일 +1390/−411, work-ui-surfaces.md 신규.
- 미커밋. worktree `mad/design-perf/lead` 보존.

## 다음에 참고
- 리뷰어가 서로 다른 처방을 낼 때(공식 예제 관찰 미완료 처리) Lead가 단일 문장을 정해 모든 lane에 배포해야 D2가 오른다.
- Codex worker는 `/tmp` 경로에서 `--skip-git-repo-check`와 `</dev/null` 없이는 시작하지 않는다.
- validate_skills.py는 표 안의 `](` 시퀀스를 링크로 파싱한다. regex 예시는 코드 스팬으로 감싼다.
