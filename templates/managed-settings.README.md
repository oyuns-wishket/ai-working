# managed-settings.json — 구조적 하드플로어 (defense-in-depth)

- 무엇: bypassPermissions/skipDangerousModePermissionPrompt로도 못 끄는 org-level `permissions.deny`. hook deny(스크립트=편집/제거 가능)의 2차 floor.
- 설치(root): `sudo mkdir -p "/Library/Application Support/ClaudeCode" && sudo cp <이 파일 옆 managed-settings.json> "/Library/Application Support/ClaudeCode/managed-settings.json"` → Claude Code 재시작.
- 한계: Bash 패턴 매칭은 best-effort(`&&`/`$()`/heredoc 우회 가능) → '보안 경계' 아닌 '사고 방지'. 설치 후 실제 deny 검증할 것.
