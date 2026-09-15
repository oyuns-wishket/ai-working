# AI와 만드는 웹 그래픽: 영상부터 게임형 경험까지

모델링 외에 그래픽 영상, 입자·유체, 설명형 단면, 공간 탐색, 게임 같은 웹 연출이 필요할 때 읽는다. 사용자는 느낌·내용·정확도를 판단하고 에이전트가 장면 설계, 자산 제작·편집, 웹 전달과 검증을 맡는다. 모르는 명칭은 [intent-to-experience.md](intent-to-experience.md)로 제안한다. 모델이 실제 필요한 경우에만 [ai-assisted-3d.md](ai-assisted-3d.md)를 추가로 읽는다.

## 1. 연출과 전달 방식을 따로 결정

모델링은 형태 제작이고, 완성 장면에는 재질·조명·카메라·합성·움직임·입력이 더해진다. 같은 물결도 영상·2D shader·실시간 3D로 만들 수 있다. 먼저 핵심 장면의 **사용자 행동 → 보이는 변화 → 완료 결과**를 정하고, 그 행동을 보존하는 경로를 추천한다.

| 웹 전달 경로 | 적합한 요구 | 제작 → 웹 연결 | 먼저 확인할 차이 |
|---|---|---|---|
| 사전 렌더 3D/그래픽 영상 | 정해진 시점의 빛·재질·복잡한 효과를 보여줌 | Blender 등에서 렌더 또는 허용된 영상 제작 → encode → HTML video와 설명 | 새 시점/부품 조작 불가; 모바일 crop·재생 정책·전송/decode 비용 |
| 스크롤 영상 / 이미지 시퀀스 | 앞뒤 scroll에 따라 준비된 장면 진행 | 카메라/장면 timeline → 영상 seek 또는 프레임 선택 → HTML 단계·CTA | seek 반응, keyframe/encode, decode·프레임 cache·메모리; 자유 회전과 구분 |
| 2D/2.5D 실시간 그래픽 | 글자·사진·캐릭터·입자·파동이 입력에 반응 | SVG/CSS/Canvas, Rive/Hana/Lottie, PixiJS 또는 shader → UI 입력/상태 | 원본의 뒷면·자유 3D 시점이 자동 생성되지 않음; runtime·효과 호환성 |
| 실시간 3D | 자유 회전·단면·분해·재질/옵션·시점 변경 | 검수한 모델/scene → Three.js 등 renderer → 입력·scroll 연결 | 형상/부품 데이터, 기기 GPU·메모리·조명 차이 |
| 게임형 체험 | 이동·조립·수집·규칙에 따라 결과 변화 | 2D/3D 자산 + 입력·상태·규칙, 필요한 경우 물리 → reset/저장/UI | 게임은 상호작용 범위이며 위 renderer 위에 구현; 모든 장식에 게임 엔진 불필요 |
| 혼합형 | 브랜드 인상과 탐색·구매·설명을 함께 제공 | hero 영상 + 조작형 제품/그래픽 구간 + 일반 HTML UI 등 | 구간별 소유권·로딩·자원 해제, 내용/CTA 연속성 |

혼합형은 후보이지 무조건 채택할 기본값이 아니다. 섹션별 목적과 예상 기기에서 비교한다. 영상이 항상 가볍거나 실시간이 항상 품질이 높다고 단정하지 않는다. 3D 작업이 필요 없는 장면에 모델·renderer를 먼저 설치하지 않는다. Motion/Anime.js는 기존 UI/연출 정책을 유지하며, 같은 속성·scroll progress·장면 시간에는 제어 주체 하나만 둔다. 엔진 내부 loop에 외부 timeline을 중복 연결하지 않는다.

## 2. 제작 도구와 실행 도구를 연결

필요한 후보만 확인하고, 플랜·API·export·권리·호스팅은 [tool-capabilities.md](tool-capabilities.md)에서 작업 시점에 검증한다. 도구 이름을 결과물처럼 납품하지 않는다.

| 제작할 것 | AI가 맡는 제작 경로 | 웹 전달과 공식 근거 |
|---|---|---|
| 3D 장면·설명·영상 | Blender Python/Geometry Nodes로 형태·재질·조명·카메라·animation 제작, render를 보고 수정 | `.blend` + 영상/시퀀스 또는 검수한 GLB; [Blender 예제 원본](https://www.blender.org/download/demo-files/), [glTF export](https://docs.blender.org/manual/en/5.0/addons/import_export/scene_gltf2.html) |
| 시각 canvas의 그래픽·상태·전환 | 사용 가능한 Spline/Hana 편집 도구·Desktop MCP로 scene과 interaction 수정 | 지원 viewer/embed/영상/export별 표현 확인; [MCP](https://docs.spline.design/generate/spline-mcp-server), [Hana export](https://docs.spline.design/hana-a-canvas-for-interactivity/assets-and-export/exporting-in-hana) |
| 캐릭터·vector 상태 반응 | Rive editor/CLI/MCP 중 실제 연결 경로로 제작·입력/상태 검수 | `.riv` runtime, 편집 원본과 publish 조건 별도 확인; [CLI](https://rive.app/docs/cli/overview), [시작/배포](https://rive.app/docs/cli/getting-started), [MCP](https://rive.app/docs/editor/ai/mcp) |
| 준비된 vector/사진/입자 효과 | 라이선스 확인한 원본을 편집하거나 SVG·Canvas·PixiJS·shader로 제작 | [Lottie 지원 기능](https://github.com/airbnb/lottie-web/wiki/Features), [PixiJS](https://pixijs.com/8.x/guides/getting-started/intro); renderer와 원본 자산 권리 분리 |
| 게임형 그래픽 | 실제 필요한 입력·규칙을 먼저 정의; 2D는 Phaser/PixiJS, 3D는 기존 Three.js 또는 PlayCanvas/Babylon 등에서 구현 | [Phaser](https://docs.phaser.io/phaser/getting-started/what-is-phaser), [PlayCanvas publishing](https://developer.playcanvas.com/user-manual/editor/publishing/web/), [Babylon](https://www.babylonjs.com/specifications/); engine와 hosted editor 비용 분리 |
| 전문 반복 그래픽·복잡한 VFX | 기존 역량/권한과 납품 필요성이 있으면 Cinema 4D MoGraph/Houdini에서 제작·렌더/변환 | [Cinema 4D](https://www.maxon.net/en/cinema-4d), [Houdini](https://www.sidefx.com/products/houdini/); 무료 로컬 대안과 실제 표현 차이 비교 |

실제 공간 캡처를 탐색할 때는 [SuperSplat](https://developer.playcanvas.com/user-manual/supersplat/)도 후보다. Gaussian splat은 의미 있는 부품·collision·편집 가능한 mesh/CAD를 자동 제공하지 않는다. 무거운 기존 Unreal 장면이 꼭 필요하면 [Pixel Streaming](https://dev.epicgames.com/documentation/unreal-engine/overview-of-pixel-streaming-in-unreal-engine)을 별도 검토한다. 서버 GPU→WebRTC 전송이므로 동시접속·지연·운영 비용을 구체화해야 하며 기본 웹 경로로 자동 선택하지 않는다.

## 3. AI 제작 → 시안 → 웹 전달

1. **장면 계획:** 대표 행동, 카메라/구도, 내용·라벨, 움직임, 필요 입력과 모바일 대안을 기존 DESIGN/구현노트에 적는다. 실제 데이터/실물과 예시·추정을 구분한다. 사운드는 필요한 경우만 설계하고 자동 소리 재생에 의존하지 않는다.
2. **짧은 제작 샘플:** 가장 어려운 핵심 장면으로 원본→export→브라우저 경로를 먼저 확인한다. 긴 영상이나 전체 세계를 만들기 전에 표현 보존·조작·기기 비용을 확인한다. 새 지출이나 미승인 업로드 없이 가능한 준비를 진행한다.
3. **동작 시안:** 기존 방향·composition 선택 안에 포함한다. 실제 시간 흐름과 요청한 클릭/scroll/입력을 체험하게 하고 replay/reset을 제공한다. 정지 mockup·외부 링크·stock placeholder만으로 최종 그래픽 품질이나 조작을 승인받았다고 기록하지 않는다. scoped 작업은 해당 구간만 비교하며 모델/영상/모션마다 별도 시안 세 묶음을 만들지 않는다.
4. **제작·수정:** 에이전트가 원본 편집과 재생·렌더 검수를 반복한다. 사용자는 “더 묵직하게”, “안쪽 구조가 잘 보이게”처럼 피드백하고 에이전트가 카메라·조명·타이밍·구조 수정으로 번역한다. 직접 할 수 없는 로그인·GUI 조작만 안내한 뒤 작업을 재개한다.
5. **웹 연결:** 승인된 방향/시안의 잠금 해제 후 프로젝트 stack·package manager로 필요한 자산/runtime만 연결한다. 내용·설명·CTA는 먼저 사용할 수 있는 HTML로 유지한다. 장면 진입/이탈과 lifecycle을 실제 route에서 확인한다.
6. **납품:** 편집 가능한 제작 원본이 있는 경로는 원본·재현 스크립트, 웹 자산·출처/권리, 장면/clip/상태 매핑과 제한을 기존 프로젝트 구조에 남긴다. 실제 웹과 승인 시안의 차이·모바일 대안·검증 결과를 함께 전달한다.

AI 영상은 보통 편집 가능한 3D 형상·카메라·부품을 제공하지 않는다. 영상만 확보했는데 자유 회전/분해까지 된다고 약속하지 않는다. DCC의 node graph·simulation·shader·compositor가 GLB로 모두 보존되는 것도 아니다. 필요한 움직임은 지원 animation으로 변환하고, 효과는 texture/영상/custom runtime 등 적합한 경로로 검증한다. “bake하면 전부 된다”로 처리하지 않는다. [glTF 사양](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html)

단면·화살표·수위·힘의 방향을 보여주는 **설명용 장면**과 검증된 계산으로 만든 **분석 시뮬레이션**은 다른 산출물이다. 예쁜 물리 효과로 구조 안전성·예측 정확도를 보장하지 않는다. 레퍼런스의 관찰 가능한 표현과 실제 제작 도구·기법에 대한 추론도 구분한다.

## 4. 전달 경로별 직접 검증

공통 웹 기준은 [verification.md](verification.md), scroll/3D 상세는 [motion-and-3d.md](motion-and-3d.md)를 따른다. 모든 경로에서 대표 모바일·touch/keyboard, reduced motion, 느린/실패한 로드, route 재진입과 자원 해제를 확인한다. 정해진 FPS/용량 수치나 desktop 결과만으로 모바일 품질을 보장하지 않는다.

- **영상:** poster·모바일 crop·codec·재생 실패와 재생/정지 수단, 필요한 자막/대체 설명을 확인한다. 자동 재생이 차단돼도 내용이 보이게 한다. 숨긴 장면은 불필요하게 재생하지 않는다. [Autoplay](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay), [video performance](https://web.dev/learn/performance/video-performance)
- **Scroll media:** 빠른 왕복·임의 위치 시작·새로고침 복원·resize에서 progress와 프레임/영상 시간이 맞는지 확인한다. 영상 seek/decode 반응을 측정하고 시퀀스는 bounded cache·해상도·선로딩·해제를 설계한다. 압축 파일 총량과 decode 후 메모리를 구분한다. 지원이 나쁘면 poster/단계 제어 등 대안을 표시한다.
- **실시간 그래픽:** 사용한 효과 조합의 WebGL/WebGPU·브라우저 호환성과 실제 frame time·입력 반응을 측정한다. feature detection과 실패 대안을 둔다. renderer의 WebGL fallback이 모든 shader/addon 호환을 보장하지 않는다. [WebGPU](https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API), [Three renderer](https://threejs.org/docs/pages/WebGPURenderer.html)
- **게임형:** 시작 방법·입력·상태/규칙·pause/reset·필요한 undo/저장·재진입을 확인한다. 키보드/터치와 일반 메뉴·skip/바로가기 등 핵심 내용 접근 경로를 둔다. 실제 쿠폰·결제·보상이 포함되면 시각 점수와 서버 검증된 업무 결과를 구분하고 해당 기능 범위를 명시한다.
- **혼합형:** 장면 간 연속성, HTML focus/anchor/scroll, 로딩 우선순위와 동시 실행 비용을 확인한다. reduced motion에서 JS/canvas/영상도 반영한다. 장면 하나의 실패가 탐색·구매·신청 전체를 막지 않게 한다.

## 5. 느낌을 고를 때 직접 볼 사례

요구에 가까운 사례만 선택한다. 아래는 표현과 제작자 설명의 근거이며 현재 기기의 실행·성능 검증 기록이 아니다. 채택 전에 실제 열어 조작하고 가져올 표현과 차이를 기록한다. 접근 실패 시 실제 읽은 문서/영상과 확인 한계를 구분한다. 오래된 API·자산 라이선스는 현재 작업에 맞게 다시 확인한다.

| 원하는 느낌 | 볼 사례 | 시안으로 가져올 판단 |
|---|---|---|
| 건축·제품 원리를 직접 이해 | [Bicycle](https://ciechanow.ski/bicycle/) | 작은 원리 단위의 slider·시점·설명 연결 |
| 영화 같은 그래픽 장면 전환 | [Monolith](https://themonolithproject.net/) · [제작기](https://tympanus.net/codrops/2025/11/29/building-the-monolith-composable-rendering-systems-for-a-13-scene-webgl-epic/) | 여러 scene의 구도·입자·전환 리듬 |
| 운전하며 세계 탐색 | [Bruno Simon](https://bruno-simon.com/) | 공간 이동·상호작용과 일반 정보 접근 |
| 직접 만들고 노는 장난감 | [Choo Choo World](https://choochooworld.com/) · [제작사](https://lusion.co/projects/choo_choo_world/) | 배치·undo·재생·결과 확인 |
| 모델 없이 반응하는 물결 | [Fluid](https://paveldogreat.github.io/WebGL-Fluid-Simulation/) · [소스](https://github.com/PavelDoGreat/WebGL-Fluid-Simulation) | 포인터 입력과 색/유체 표현, 배경의 가독성 |
| 사진에서 살아나는 입자 | [Until Labs](https://www.untillabs.com/) · [제작기](https://tympanus.net/codrops/2025/12/10/simulating-life-in-the-browser-creating-a-living-particle-system-for-the-untillabs-website/) | 사진·로고를 활용한 입력 반응과 복귀 |
| 전문 제작 도구로 만든 생태 공간 | [Of the Oak](https://oftheoak.co.uk/) · [제작사](https://lusion.co/projects/of_the_oak/) | 제작 원본을 웹용 데이터로 변환하는 방식 |
