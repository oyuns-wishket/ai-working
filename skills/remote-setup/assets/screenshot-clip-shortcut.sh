#!/bin/bash
# 스크린샷 단축키 스왑 — 선택영역 캡쳐를 "파일 저장" 대신 "클립보드 복사"로.
# 기본 macOS: ⌘⇧4=선택→파일(id30), ⌃⌘⇧4=선택→클립보드(id31).
# 이 스크립트: ⌘⇧4=선택→클립보드(id31), ⌃⌘⇧4=선택→파일(id30) 으로 스왑.
# 이유: 클립보드 이미지 미니 전송 워크플로(⌘⇧4 → 오른쪽⌘V)를 한 키로 편하게.
# parameters = [keychar(52='4'), keycode(21='4'), modifiers].
#   1179648 = ⌘⇧ (cmd+shift)         → ⌘⇧4
#   1441792 = ⌘⇧⌃ (cmd+shift+ctrl)   → ⌘⇧⌃4
set -e

# id31: 선택영역 → 클립보드 = ⌘⇧4
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 31 "
<dict><key>enabled</key><integer>1</integer><key>value</key><dict><key>type</key><string>standard</string><key>parameters</key><array><integer>52</integer><integer>21</integer><integer>1179648</integer></array></dict></dict>"

# id30: 선택영역 → 파일 = ⌘⇧⌃4
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 30 "
<dict><key>enabled</key><integer>1</integer><key>value</key><dict><key>type</key><string>standard</string><key>parameters</key><array><integer>52</integer><integer>21</integer><integer>1441792</integer></array></dict></dict>"

# 적용 (재로그인 없이 반영 시도)
/System/Library/PrivateFrameworks/SystemAdministration.framework/Resources/activateSettings -u 2>/dev/null || true
killall cfprefsd 2>/dev/null || true

echo "스크린샷 단축키 스왑 완료: ⌘⇧4=선택→클립보드, ⌘⇧⌃4=선택→파일"
echo "반영 안 되면 로그아웃→로그인 1회. 확인: 시스템 설정 > 키보드 > 단축키 > 스크린샷"
