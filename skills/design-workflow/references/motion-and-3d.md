# 웹 모션과 3D 체험

웹 모션의 기본 정책과 시안 선택은 [motion-design.md](motion-design.md)를 따른다. 이 문서는 3D 장면의 runtime·scroll·성능 검증에서 읽는다. 영상·시퀀스·입자·게임형과 실시간 3D를 선택할 때는 [graphics-production.md](graphics-production.md), 모델 제작이 필요하면 [ai-assisted-3d.md](ai-assisted-3d.md), 외부 서비스는 [tool-capabilities.md](tool-capabilities.md)로 실제 사용 가능한 경로를 정한다.

## 모션 선택과 이 문서의 경계

모션 도구 선택·timing/easing·GSAP 예외 조건은 [motion-design.md](motion-design.md)가 소유한다. 이 문서는 같은 기본값을 다시 정의하지 않고 **3D 장면의 runtime·scroll 소유권·자산 파이프라인·성능·검증**을 소유한다. 게이트와 도구 기본값은 [SKILL.md](../SKILL.md)를 따른다.

`audit`이면 아래 제작·구현·검증 절을 기존 자산·실행 중 화면의 읽기 전용 관찰에만 적용한다. export·최적화·설치·source/기록 파일 쓰기 없이 확인한 결과와 미실행 범위를 대화로 보고한다.

GSAP은 Anime.js onScroll/Motion useScroll로 구현 불가한 기능을 공식 문서·실측으로 확인하고 DESIGN에 예외로 기록한 경우에만 추가한다. 예외 근거와 담당 속성의 기록은 [motion-design.md](motion-design.md)의 구현 계약을 따른다.

native page scroll과 필요 시 CSS sticky를 바탕으로 선택한 timeline의 진행률을 장면에 전달한다. Motion이 이미 progress를 소유하면 그 값을 소비하고 별도 scroll 제어기를 만들지 않는다. Motion의 별도 Three.js premium/early-access 통합과 무료 progress 연결을 혼동하지 않는다.

기존 공식 참조: [Motion](https://motion.dev/docs/react), [Anime.js scroll](https://animejs.com/documentation/events/onscroll/), [Anime.js sync](https://animejs.com/documentation/events/onscroll/scrollobserver-synchronisation-modes/), [Motion useScroll](https://motion.dev/docs/react-use-scroll), [GSAP ScrollTrigger](https://gsap.com/docs/v3/Plugins/ScrollTrigger/). 설치 사실만으로 이 후보를 함께 연결하지 않는다.

## 3D는 세 역할로 나눈다

| 역할 | 후보와 조건 | 확인할 근거 |
|---|---|---|
| 모델 확보·제작 | AI가 권리 확인한 자산 확보 또는 전문 도구 제작·편집·검수를 수행. 정확한 제품은 원본/치수, 가상 모델은 허용된 AI 생성이나 Blender 제작 | [AI 협업 제작](ai-assisted-3d.md), [Blender glTF](https://docs.blender.org/manual/en/5.0/addons/import_export/scene_gltf2.html), [Meshy](https://docs.meshy.ai/en) |
| 브라우저에서 표시·조명·카메라 | Three.js; React 프로젝트는 React Three Fiber/Drei를 조건부 검토. 시각 편집을 원하면 Spline | [GLTFLoader](https://threejs.org/docs/pages/GLTFLoader.html), [R3F](https://github.com/pmndrs/react-three-fiber), [Spline](https://docs.spline.design/) |
| 스크롤과 동작 연결 | 기존 모션 도구(Anime.js/Motion); 기록된 예외만 GSAP. [motion-design.md](motion-design.md)의 선택 결과를 적용하며 R3F 내부 scroll container가 필요한 경우에만 Drei ScrollControls 검토 | [ScrollControls](https://drei.docs.pmnd.rs/controls/scroll-controls), [Spline scroll](https://docs.spline.design/interaction-states-events-and-actions/events/scroll-event) |

Spline의 페이지 기반 `Scroll` 유형은 공식 문서상 Viewer export 제약이 있다. 현재 export 방식과 페이지 scroll 연동이 맞는지 확인한다. Drei ScrollControls가 별도 HTML scroll container를 생성하므로 기존 페이지 스크롤·anchor·키보드와 충돌하는지 확인한다. Meshy는 외부 생성 서비스/API이며 브라우저 내 모델링 라이브러리가 아니다. 사용자 제공 자산의 외부 전송·과금은 승인된 범위에서만 수행한다.

## 모델이 '변한다'는 뜻을 먼저 확정

- **회전·이동·확대**: object/camera transform을 제어한다.
- **분해·조립**: 분리된 부품 mesh, 의미 있는 이름·pivot·기준 위치가 필요하다. 단일 mesh AI 결과로 준비됐다고 가정하지 않는다.
- **형태 변형**: morph targets/shape keys, rig 또는 shader 등 방식과 데이터가 필요하다. 임의로 생성한 두 모델이 자동 morph 호환이라고 약속하지 않는다.
- **재질 변화**: material parameter·texture·조명 상태를 제어하고 실제 제품 색/재질 정확도 요구를 확인한다.
- **정해진 애니메이션**: export된 clip의 시간과 scroll progress를 연결한다. 자동 재생 mixer와 scroll이 동시에 시간을 진행시키지 않게 한다.

GLB/glTF로 내보냈다고 원본의 모든 shader·modifier·constraint가 보존되는 것은 아니다. 최종 자산에서 부품·animation·재질·스케일을 실제 확인한다. AI 생성은 검토할 초안으로 취급하고 치수·부품 구조·rig/변형 데이터를 보장하지 않는다.

단순 상품 회전·색상·AR 중심이면 [model-viewer](https://modelviewer.dev/)를 검토한다. 정해진 카메라의 복잡한 연출은 사전 렌더 영상/시퀀스도 후보지만 자유 회전과 같은 결과는 아니다. 사용자의 핵심 조작을 바꾸는 대안은 차이를 보여주고 결정한다.

## Runtime·scroll 소유권 계약

1. route/구간마다 **같은 scroll progress·camera·속성에 제어기 하나**를 지정한다. 값의 생산자와 소비자를 구분한다. Motion이 만든 progress를 Anime.js timeline이 읽는다면 별도 observer로 같은 progress를 다시 만들지 않는다.
2. 사용자가 자유 회전하는 구간이면 camera를 사용자 controls가 소유한다. scroll 연출로 복귀하면 controls의 쓰기를 중단하고 현재 pose에서 정한 복귀 상태로 넘긴다. 두 제어기를 동시에 활성화하지 않는다.
3. scroll이 clip 시간을 소유하면 자동 재생 mixer의 시간 진행을 중단한다. 자동 재생을 다시 켤 때는 scroll 쓰기를 중단한 뒤 소유권을 넘긴다.
4. 페이지 scroll이 기준이면 별도 내부 scroll container를 만들기 전에 anchor·keyboard·touch와 복원 위치를 검증한다. 내부 scroll이 필요하면 그 구간과 탈출/복귀 동작을 기록한다.
5. 장면 이탈/unmount이면 소유한 listener·timeline·render loop와 GPU 자원을 정리한다. 다른 화면이 쓰는 공유 asset은 마지막 사용자가 해제하는 기존 수명 계약을 따른다.

| 구간·대상 속성 | 단일 쓰기 소유자 | 입력/읽기 소비자 | 전환·초기화 조건 | 해제 책임 |
|---|---|---|---|---|
| page scroll progress | 선택한 scroll 제어기 하나 | scene timeline·HTML 단계 | 새로고침/anchor/resize 때 현재 위치로 계산 | 제어기를 만든 route/component |
| camera pose | scene timeline 또는 사용자 controls 중 하나 | renderer | 자유 회전 진입/종료 때 이전 쓰기 중단 | scene owner |
| clip time·부품 transform | scroll timeline 또는 자동 재생 중 하나 | 모델/renderer | replay/reset·역방향 입력에도 현재 progress에 대응 | animation owner |
| UI layout·chart geometry | 각 UI/차트 담당 | scene는 필요한 상태만 읽음 | 필터·선택 결과에 대응 | UI/차트 component |

실제 도구·대상 이름으로 표를 채우고 기존 DESIGN의 renderer/scroll owner 결정에 연결한다. `audit`이면 표의 관찰을 대화로만 보고한다.

## 장면 계획과 구현

3D scroll 장면의 시안에는 실제 scroll/interaction 미리보기와 replay를 반드시 포함한다. 정지 다각도 렌더만으로는 시안 게이트를 통과할 수 없다.

새 그래픽·3D 방향의 동작 시안 세 개에는 [graphics-production.md의 동작 시안 기준](graphics-production.md#3-ai-제작--시안--웹-전달)을 적용한다. 세 안은 장면 구조(카메라 경로·구간 순서)·조작/반응 방식·전달 경로 중 최소 두 가지에서 달라야 하며 색·조명 강도·easing만 바꾼 안은 부적합이다. 같은 콘텐츠·대표 행동과 승인된 범위 안에서 비교하며, 세 안의 각 쌍(A/B·A/C·B/C)에 이 기준을 적용한다.

- 제품 목적에 맞춰 scroll 구간별 카메라·모델 상태·HTML 설명·CTA를 기록한다. 시작/중간/끝 예시만으로 중요한 전환을 놓치지 않는다.
- 연출 검증은 분리된 시안 경로에서 한다. 모바일 정책과 fallback을 포함해 승인된 composition에 반영한다.
- asset bytes·texture 크기·device pixel ratio·draw call·GPU 비용은 실제 대상 기기와 장면을 보고 예산을 정한다. 보편적인 파일 크기나 FPS를 성능 보장으로 쓰지 않는다.
- heavy asset은 필요한 구간에 로드하고 poster·설명·CTA를 먼저 제공한다. WebGL 미지원/실패·느린 network에도 핵심 내용과 다음 행동을 유지한다.
- resize이면 viewport·renderer 크기·카메라·scroll 구간을 다시 계산하고 같은 progress에 맞는 장면을 유지한다. 재생성하는 listener/timeline은 이전 것을 먼저 해제한다. unmount·route 전환이면 소유한 listener/timeline·render loop·GPU 자원을 해제한다. resize만으로 사용 중인 자산을 dispose하거나 공유 자산을 다른 화면이 쓰는 동안 해제하지 않는다.
- 사용자 직접 회전과 scroll camera가 경쟁하지 않게 한다. 매 프레임 geometry/React state를 불필요하게 새로 만들지 않는다.
- 원본을 보존하고 [glTF Transform](https://gltf-transform.dev/) 등으로 필요한 최적화만 적용한다. mesh 압축과 실제 polygon/draw-call 감소를 구분하고 decoder/transcoder도 배포한다. 부품 이름·계층·morph·clip을 join/flatten으로 잃지 않았는지 전후 검사한다.
- 정지 장면의 demand rendering은 외부 엔진이 값을 바꿀 때 invalidate 연결을 포함한다. 영상·시퀀스 대안도 seek·decode·메모리를 실제 기기에서 확인한다.

## 검증

[verification.md](verification.md)는 공통 실행 순서·증거 형식과 목적별 검증 요약을 소유한다. 이 절은 3D runtime 검증의 상세이며, 모델 자체의 검수는 [ai-assisted-3d.md](ai-assisted-3d.md)를 함께 적용한다. 모션의 OS 설정 변경·연속 입력 기준은 [motion-design.md](motion-design.md)를 따른다.

1. 같은 route·viewport·data/state·theme·auth·자산·카메라 조건에서 승인된 동작 시안과 시작/전환/완료를 대조한다. 공식 예제 관찰·채택 기록은 모델 제작이면 [ai-assisted-3d.md](ai-assisted-3d.md#공식-예제-관찰과-채택-기록), 전달 경로 선택이면 [graphics-production.md](graphics-production.md#공식-예제-관찰과-채택-기록)의 표에 연결한다. 접근 실패와 제작 도구 검수만으로 공식 실행 예제 관찰을 완료 처리하지 않는다.
2. 구현 전 대표 기기와 장면의 수용 예산을 정한다. 입력 반응·frame time·asset/texture bytes·draw call·메모리 중 병목에 관련된 항목을 선택하고 도구·측정 구간·network/cache·반복 조건을 기록한다. 보편적인 FPS/용량을 통과 기준으로 복사하지 않는다.
3. 아래 조작과 실패 조건을 실행한다. 실측이 예산을 넘으면 자산·로딩·render loop를 조정하고 같은 조건에서 다시 측정한다. 요청한 자유 조작을 영상으로 바꿔야 하면 전달 경로의 차이를 구체화해 결정받는다.

- 앞/뒤 scroll, 빠른 구간 이동, resize, 새로고침 시 복원 위치, anchor와 키보드 이동, touch를 확인한다. 특정 순서로 내려야만 맞는 animation은 실패다.
- 모델 로드 실패·느린 로드, reduced motion, WebGL fallback에서 핵심 콘텐츠가 남는지 확인한다. reduced motion은 CSS만 끄고 JS/canvas motion을 남겨두지 않는다. [Motion accessibility](https://motion.dev/docs/react-accessibility)
- route 재진입 시 canvas/listener 중복·console 오류·자원 증가를 확인한다. 대표 모바일에서 프레임 시간과 조작 반응을 측정하고 기기/조건을 기록한다.
- 실제 제품 형상·부품·재질 정확도는 원본 또는 사용자 확인과 대조한다. 예쁜 렌더링만으로 정확성·사용성까지 통과했다고 보고하지 않는다.

직접 볼 예: [scroll에 따라 접히는 상자](https://tympanus.net/Tutorials/OnScrollFoldingCardboardBox/), [작성자 설명](https://tympanus.net/codrops/2022/12/13/how-to-code-an-on-scroll-folding-3d-cardboard-box-animation-with-three-js-and-gsap/), [Spline scroll demo](https://viewer-scroll-event.framer.website/), [Motion examples](https://motion.dev/examples). 오래된 예제의 API·라이선스는 현재 프로젝트 버전으로 다시 확인한다.

아래 상세 표는 [verification.md](verification.md)의 공통 검증 표 `결과`에 증거로 연결한다. 공통 표의 명령/route·조건·통과/실패/미실행/N/A·미실행 사유를 대체하지 않는다.

| 검증 구간·조작 | 기기·브라우저·network/cache·자산 조건 | 측정 도구·기준/수용 예산 | 전후 관찰·실측·증거 | 판정·누락·후속 |
|---|---|---|---|---|
| scroll 왕복·자유 회전 전환·route 재진입 등 | 실제 비교 조건 | frame/input·bytes·자원 수 등 선택한 항목 | 수치와 시작/전환/완료 재생 기록 | 통과 / 실패 / 미실행 및 이유 |

route 재진입 횟수와 전후 canvas/listener·자원 수를 기록한다. 반복할수록 자원이 증가하면 소유·해제 계약을 다시 확인한다. 개발 도구에서 측정할 수 없는 GPU 항목은 미측정으로 표시하고 추측값으로 채우지 않는다. 필요한 검사나 승인 표현이 빠졌으면 완료로 보고하지 않는다.
