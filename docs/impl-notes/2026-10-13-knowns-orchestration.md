# knowns 호출 주체를 dev-protocol 하나로 (2026-10-13)

## 목표와 요청
사용자가 "계획 → 개발 → 배포 → 지식정리" 흐름에서 `knowns`가 어디서 호출되는지 확인했다. `feature-flow`가
`knowns`를 직접 호출하고 예전 승인 방식(의미·목표·기여 확정 후 exact write plan 별도 승인)을 적고 있어, 사용자가
"feature-flow 낡은 부분은 수정하고 오케스트레이션 잘잡아줘"를 요청했다. 원격 반영과 다른 Mac 최신화까지 승인.
hook으로 knowns 실행을 강제하는 안은 사용자가 "너무 과해"로 기각했다.

## 변경
- `skills/dev-protocol/SKILL.md`: "프로젝트 workflow skill과의 관계"에 클로즈아웃 호출 주체를 명시. `knowns`는 §6에서만
  호출하고 workflow·도메인 skill은 배포 증거와 후보 힌트만 넘긴다. 사용자 직접 요청은 예외.
- `skills/feature-flow/SKILL.md` "종료 지식화": 직접 호출과 별도 write plan 승인 문구를 제거하고, 개발 통합까지는
  §5.6 HANDOFF 후보, 운영 검증 후에는 운영 URL·헬스체크·migration 결과를 증거로 §6을 실행하도록 정리.
- `skills/paseo-setup/SKILL.md`, `skills/online-channel-guide/SKILL.md`: 같은 직접 호출·별도 승인 문구를 위임 형태로
  바꾸고 skill 고유의 후보 힌트만 남겼다. `design-workflow`는 이미 위임 형태라 그대로 둔다.

## 근거와 기각한 대안
- 호출 지점이 여럿이면 승인 방식이 skill마다 달라지고(이번처럼 낡은 2단계 승인), 중복 방지를 `KNOWNS:` 표식에만
  의존한다. 호출 주체를 하나로 두면 승인 규칙은 `knowns`/`production-closeout.md` 한 곳만 고치면 된다.
- 실행 강제 hook: 사용자가 기각. 문서 지시 준수에 의존한다는 한계는 그대로다.

## 검증
- `python3 scripts/validate_skills.py`: passed (24 skills)
- `python3 scripts/public_audit.py --history`: passed (234 tracked files + full history)
- `grep -rn knowns skills/` 로 `knowns` 자신과 dev-protocol 외에 직접 호출 문구가 남지 않았는지 확인: 남은 직접 호출 문구 없음.
- push 후 `public-safety` workflow 결과 확인.

## 남은 일
- 없음. 실제 운영배포 closeout에서 흐름을 다시 돌려 보지는 않았다.
