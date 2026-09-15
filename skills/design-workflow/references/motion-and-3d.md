# 웹 모션과 3D 체험

웹 모션의 기본 정책과 시안 선택은 [motion-design.md](motion-design.md)를 따른다. 이 문서는 3D 장면의 runtime·scroll·성능 검증에서 읽는다. 영상·시퀀스·입자·게임형과 실시간 3D를 선택할 때는 [graphics-production.md](graphics-production.md), 모델 제작이 필요하면 [ai-assisted-3d.md](ai-assisted-3d.md), 외부 서비스는 [tool-capabilities.md](tool-capabilities.md)로 실제 사용 가능한 경로를 정한다.

## 모션 선택

| 요구 | 후보 | 구분할 점 |
|---|---|---|
| 앱 상태·layout·gesture 전환 | [Motion](https://motion.dev/docs/react) | 웹 UI 기본 경로; stack별 문서를 확인하고 기존 승인 패턴 재사용 |
| SVG·여러 요소의 순차 연출·3D scroll timeline | [Anime.js](https://animejs.com/documentation/events/onscroll/) | 연출 요청 시 설치·연결; 객체 수치와 timeline을 제어하며 모델을 자동 제작하지 않음 |
| 페이지 구간 고정·복잡한 scroll timeline | [GSAP ScrollTrigger](https://gsap.com/docs/v3/Plugins/ScrollTrigger/) | trigger(시작)와 scrub(진행률 연결)을 구분; renderer가 아님 |

같은 scroll progress·camera·transform에 둘 이상의 제어기를 붙이지 않는다. 기존 Anime.js/Motion으로 충분하면 GSAP을 추가하지 않는다. smooth-scroll 도구는 기본 설치하지 않는다.

기본 웹 연출은 native page scroll과 필요 시 CSS sticky를 사용하고 Anime.js timeline의 진행률을 장면 상태에 연결한다. Motion이 이미 progress를 소유하면 그 값을 재사용할 수 있다. [Anime.js sync](https://animejs.com/documentation/events/onscroll/scrollobserver-synchronisation-modes/), [Motion useScroll](https://motion.dev/docs/react-use-scroll). Motion의 별도 Three.js premium/early-access 통합과 무료 progress 연결을 혼동하지 않는다.

모션은 관계·변화·피드백을 설명해야 한다. 업무 화면의 짧은 피드백은 대략 120–240ms를 출발점으로 삼되 기존 토큰과 목적에 맞춘다. 의도적 scroll story를 이 시간 안에 끝내도록 강제하지 않는다. 반복 업무를 기다리게 하는 등장 애니메이션은 줄이고, 새 조작이 오면 자연스럽게 이어지게 한다.

## 3D는 세 역할로 나눈다

| 역할 | 후보와 조건 | 확인할 근거 |
|---|---|---|
| 모델 확보·제작 | AI가 권리 확인한 자산 확보 또는 전문 도구 제작·편집·검수를 수행. 정확한 제품은 원본/치수, 가상 모델은 허용된 AI 생성이나 Blender 제작 | [AI 협업 제작](ai-assisted-3d.md), [Blender glTF](https://docs.blender.org/manual/en/5.0/addons/import_export/scene_gltf2.html), [Meshy](https://docs.meshy.ai/en) |
| 브라우저에서 표시·조명·카메라 | Three.js; React 프로젝트는 React Three Fiber/Drei를 조건부 검토. 시각 편집을 원하면 Spline | [GLTFLoader](https://threejs.org/docs/pages/GLTFLoader.html), [R3F](https://github.com/pmndrs/react-three-fiber), [Spline](https://docs.spline.design/) |
| 스크롤과 동작 연결 | 기존 모션 도구 또는 GSAP; R3F 내부 scroll container라면 Drei ScrollControls 검토 | [ScrollControls](https://drei.docs.pmnd.rs/controls/scroll-controls), [Spline scroll](https://docs.spline.design/interaction-states-events-and-actions/events/scroll-event) |

Spline의 페이지 기반 `Scroll` 유형은 공식 문서상 Viewer export 제약이 있다. 현재 export 방식과 페이지 scroll 연동이 맞는지 확인한다. Drei ScrollControls가 별도 HTML scroll container를 생성하므로 기존 페이지 스크롤·anchor·키보드와 충돌하는지 확인한다. Meshy는 외부 생성 서비스/API이며 브라우저 내 모델링 라이브러리가 아니다. 사용자 제공 자산의 외부 전송·과금은 승인된 범위에서만 수행한다.

## 모델이 '변한다'는 뜻을 먼저 확정

- **회전·이동·확대**: object/camera transform을 제어한다.
- **분해·조립**: 분리된 부품 mesh, 의미 있는 이름·pivot·기준 위치가 필요하다. 단일 mesh AI 결과로 준비됐다고 가정하지 않는다.
- **형태 변형**: morph targets/shape keys, rig 또는 shader 등 방식과 데이터가 필요하다. 임의로 생성한 두 모델이 자동 morph 호환이라고 약속하지 않는다.
- **재질 변화**: material parameter·texture·조명 상태를 제어하고 실제 제품 색/재질 정확도 요구를 확인한다.
- **정해진 애니메이션**: export된 clip의 시간과 scroll progress를 연결한다. 자동 재생 mixer와 scroll이 동시에 시간을 진행시키지 않게 한다.

GLB/glTF로 내보냈다고 원본의 모든 shader·modifier·constraint가 보존되는 것은 아니다. 최종 자산에서 부품·animation·재질·스케일을 실제 확인한다. AI 생성은 검토할 초안으로 취급하고 치수·부품 구조·rig/변형 데이터를 보장하지 않는다.

단순 상품 회전·색상·AR 중심이면 [model-viewer](https://modelviewer.dev/)를 검토한다. 정해진 카메라의 복잡한 연출은 사전 렌더 영상/시퀀스도 후보지만 자유 회전과 같은 결과는 아니다. 사용자의 핵심 조작을 바꾸는 대안은 차이를 보여주고 결정한다.

## 장면 계획과 구현

- 제품 목적에 맞춰 scroll 구간별 카메라·모델 상태·HTML 설명·CTA를 기록한다. 시작/중간/끝 예시만으로 중요한 전환을 놓치지 않는다.
- 연출 검증은 분리된 시안 경로에서 한다. 모바일 정책과 fallback을 포함해 승인된 composition에 반영한다.
- asset bytes·texture 크기·device pixel ratio·draw call·GPU 비용은 실제 대상 기기와 장면을 보고 예산을 정한다. 보편적인 파일 크기나 FPS를 성능 보장으로 쓰지 않는다.
- heavy asset은 필요한 구간에 로드하고 poster·설명·CTA를 먼저 제공한다. WebGL 미지원/실패·느린 network에도 핵심 내용과 다음 행동을 유지한다.
- 리사이즈·unmount·route 전환 시 scroll listener/timeline과 소유한 GPU 자원을 정리한다. 공유 자산을 다른 화면이 쓰는 동안 dispose하지 않는다.
- 사용자 직접 회전과 scroll camera가 경쟁하지 않게 한다. 매 프레임 geometry/React state를 불필요하게 새로 만들지 않는다.
- 원본을 보존하고 [glTF Transform](https://gltf-transform.dev/) 등으로 필요한 최적화만 적용한다. mesh 압축과 실제 polygon/draw-call 감소를 구분하고 decoder/transcoder도 배포한다. 부품 이름·계층·morph·clip을 join/flatten으로 잃지 않았는지 전후 검사한다.
- 정지 장면의 demand rendering은 외부 엔진이 값을 바꿀 때 invalidate 연결을 포함한다. 영상·시퀀스 대안도 seek·decode·메모리를 실제 기기에서 확인한다.

## 검증

- 앞/뒤 scroll, 빠른 구간 이동, resize, 새로고침 시 복원 위치, anchor와 키보드 이동, touch를 확인한다. 특정 순서로 내려야만 맞는 animation은 실패다.
- 모델 로드 실패·느린 로드, reduced motion, WebGL fallback에서 핵심 콘텐츠가 남는지 확인한다. reduced motion은 CSS만 끄고 JS/canvas motion을 남겨두지 않는다. [Motion accessibility](https://motion.dev/docs/react-accessibility)
- route 재진입 시 canvas/listener 중복·console 오류·자원 증가를 확인한다. 대표 모바일에서 프레임 시간과 조작 반응을 측정하고 기기/조건을 기록한다.
- 실제 제품 형상·부품·재질 정확도는 원본 또는 사용자 확인과 대조한다. 예쁜 렌더링만으로 정확성·사용성까지 통과했다고 보고하지 않는다.

직접 볼 예: [scroll에 따라 접히는 상자](https://tympanus.net/Tutorials/OnScrollFoldingCardboardBox/), [작성자 설명](https://tympanus.net/codrops/2022/12/13/how-to-code-an-on-scroll-folding-3d-cardboard-box-animation-with-three-js-and-gsap/), [Spline scroll demo](https://viewer-scroll-event.framer.website/), [Motion examples](https://motion.dev/examples). 오래된 예제의 API·라이선스는 현재 프로젝트 버전으로 다시 확인한다.
