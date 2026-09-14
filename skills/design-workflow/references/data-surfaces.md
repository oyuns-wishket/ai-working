# 데이터 대시보드와 업무 표

검토일: 2026-09-14. 수치를 통해 어떤 결정을 하는지 먼저 확인한다. 기존 데이터 계약을 새 디자인에 맞춰 바꾸지 않는다.

## 지표와 시각 표현

- 지표 이름·정의·단위·시간대·기간·비교 기간·집계 범위·갱신 시점을 확인한다. API/쿼리로 확인 가능한 것은 사용자에게 되묻지 않는다.
- 0, null/누락, 조회 중, 조회 실패를 구분한다. 분모 0의 증감률이나 미수집 데이터를 임의 0%로 표시하지 않는다.
- 카드·차트·상세 표가 같은 필터와 집계를 사용해야 한다. 샘플 데이터는 샘플로 표시한다.
- 추세는 선, 항목 비교는 막대, 정확한 값·검색·업무 처리는 표가 출발점이다. 목표/분모가 없는데 장식용 gauge를 넣지 않는다. 복잡한 차트는 사용자의 판단을 더 쉽게 할 때만 선택한다.
- 단위·축·범례·tooltip·색의 의미를 일관되게 한다. 축 절단과 집계/샘플링으로 의미가 달라지면 명시한다. 색 외에 label/pattern을 제공한다.

## 후보 선택

| 후보 | 검토할 상황 | 범위·제약 | 공식 근거 |
|---|---|---|---|
| 기존 표·차트 / HTML·CSS | KPI·작은 비교, 이미 구현된 시각화 | 새 의존성 없이 가능 여부 먼저 확인 | 프로젝트 소스·실행 화면 |
| Bklit UI | React/shadcn 환경에서 차트의 시각 완성도를 높일 때 | 컴포넌트와 Studio의 배포/라이선스를 구분; 도입 전 실제 소스·접근성 검증 | [Docs](https://bklit.com/docs), [source/licenses](https://github.com/bklit/bklit-ui) |
| Recharts | React에서 조합형 SVG 차트가 맞을 때 | 설치 버전의 API·키보드 지원과 데이터량을 확인; 기존 chart wrapper 우선 | [API](https://recharts.github.io/en-US/api/), [accessibility](https://github.com/recharts/recharts/blob/main/storybook/stories/API/Accessibility.mdx) |
| Apache ECharts | 확대·탐색·다양한 차트가 실제로 필요할 때 | 대표 데이터로 성능 측정; ARIA·텍스트 요약·패턴을 명시 설정/확인 | [Examples](https://echarts.apache.org/examples/en/index.html), [accessibility](https://echarts.apache.org/handbook/en/best-practices/aria/) |
| TanStack Table | 정렬·필터·페이지 처리 등 복잡한 업무 표 | headless 로직이다. markup·디자인·접근성은 직접 구현; 가상화는 별도 선택 | [Overview](https://tanstack.com/table/v8/docs/overview) |

표의 도구를 한꺼번에 넣지 않는다. 새 차트가 필요하면 기존 engine을 우선하고, 두 engine이 꼭 필요할 때만 중복 비용을 기록한다. headless 도구·차트 컴포넌트·데이터 수집 시스템을 혼동하지 않는다.

## 직접 검증

1. 대표 데이터에서 카드 합계·차트·표의 값을 원본 집계와 대조한다. 전체 데이터와 현재 page 합계를 혼동하지 않는다.
2. 기간/필터 변경, drill-down, sorting/pagination의 실제 범위를 확인한다. server pagination인데 현재 page만 정렬되는 회귀를 막는다.
3. empty·한 건·음수·매우 큰 값·누락·느린 요청·오류 중 해당하는 상태를 확인한다. 요청 순서가 역전돼 오래된 값이 덮어쓰지 않는지 확인한다.
4. 좁은 화면·긴 범례·숫자 정밀도·tooltip clipping·keyboard/touch 접근을 확인한다. 핵심 값을 텍스트나 표로도 읽을 수 있게 한다.
5. 많은 데이터가 실제 요구이면 대표 규모에서 렌더·필터 반응을 측정한다. 가상화/샘플링은 선택·focus·내보내기·수치 의미를 보존하는지 함께 검증한다.

시각 스냅샷만으로 데이터 정확성까지 통과했다고 보고하지 않는다.
