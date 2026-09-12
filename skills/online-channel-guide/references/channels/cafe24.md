# 카페24 (Cafe24 Admin API) — 온보딩 카드

자사몰 솔루션. 마켓플레이스가 아니라 **몰 단위(per-mall)** 연동이다.
단, ⚠️ **응답에는 자사몰 주문만 오지 않는다** — 마켓플러스로 연동한 외부 마켓 주문과
자사몰 간편구매 주문이 한 응답에 섞여 온다. 아래 12절 참조.

| 항목 | 값 |
| --- | --- |
| 내부코드 | `cafe24` |
| 온보딩 등급 | `SELF` (개발자센터 앱 등록 + 브라우저 1회 동의) |
| 확인일 | 2026-07-31 |
| 출처 | 카페24 개발자센터 `developers.cafe24.com`, 실측 |

## 1. 선행조건

- 카페24 쇼핑몰(`mall_id`)과 운영자 계정.
- 카페24 개발자센터 계정.

## 2. 신청 경로

개발자센터 → 앱 생성 → **개발 정보**에서 `client_id`·`client_secret` 확인,
`redirect URI` 등록, **scope**(예: `mall.read_order`, `mall.write_order`) 설정. `3rd` / `live`

이후 **브라우저 1회 동의**가 필요하다(다른 채널과 가장 다른 점).

```text
1) GET https://{mall_id}.cafe24api.com/api/v2/oauth/authorize
     ?response_type=code&client_id=…&state=…&redirect_uri=…&scope=mall.read_order,mall.write_order
2) 동의 → redirect_uri 로 ?code=…&state=…   (인증코드 유효 1분)
3) POST https://{mall_id}.cafe24api.com/api/v2/oauth/token
     헤더 Authorization: Basic base64(client_id:client_secret)
     body grant_type=authorization_code&code=…&redirect_uri=…
```

## 3. 심사·리드타임

심사 없음. 앱 등록과 동의만 끝나면 즉시. `live`

## 4. 발급 결과물

`client_id`, `client_secret`, 그리고 동의 후 `access_token` + `refresh_token`.
응답에 `mall_id`, `scopes[]`, 만료시각이 함께 온다. `live`

⚠️ 인증에 쓰는 쌍은 **`client_id`/`client_secret`**이다.
`front_api_key`/`service_key`는 Front API·웹훅 서명용으로 **다른 것**이다. `live`

## 5. 키 수명·회전 — 이 채널의 최대 리스크

- 인증코드 **1분**, access token **약 2시간**, refresh token **약 14일**. `live`
- ⚠️ **refresh는 refresh_token을 회전시킨다.** 갱신 응답에 NEW access + NEW refresh가
  함께 오고 **기존 refresh_token은 즉시 무효**가 된다. 회전분을 매 사이클 영속화하지
  않으면 다음 갱신에서 **lock-out**되어 브라우저 동의부터 다시 해야 한다. `live`
- ⚠️ 따라서 **크론이 최소 14일에 1회 이상 반드시 돌아야 한다.** 장기 중단 = 재동의. `live`
- 토큰 저장소는 파일이면 권한 `0600`, 전체 덮어쓰기 저장(부분 갱신 금지)으로 만든다. `live`

## 6. 네트워크 요건

⚠️ **IP 화이트리스트 없음.** OAuth 토큰 기반이라 호출 IP 등록이 없다
(네이버·쿠팡·11번가·롯데온과 다른 점, 확인됨). 서버 이전이 자유롭다. `live`

## 7. 권한·스코프

scope 단위(`mall.read_order`, `mall.write_order` 등). **범위를 넓히면 재동의가 필요**하므로
필요한 scope를 처음 동의에서 함께 받는다. `live`

## 8. 역할 분담

| 주체 | 할 일 |
| --- | --- |
| `[USER]` | 개발자센터 앱 생성, scope·redirect URI 설정, **브라우저 동의 1회** |
| `[AI]` | authorize URL 생성, code 교환, 회전 토큰 저장소, 어댑터, probe |
| `[3RD]` | 몰 운영자가 고객사면 동의 주체가 고객사 (대기 항목) |

부트스트랩은 `--print-url`(authorize URL 출력) → 사용자 동의 → `--code <code>` 교환
형태의 헬퍼로 만들면 사용자 조작을 1회로 줄일 수 있다. `live`

## 9. 첫 호출 검증

토큰 교환 성공 후 주문 목록을 최근 짧은 창으로 1회 read.
헤더 `X-Cafe24-Api-Version`을 고정 값으로 명시한다(버전 미지정 시 동작이 달라질 수 있다). `live`

## 10. 함정

- 호스트가 **per-mall**(`https://{mall_id}.cafe24api.com`)이다. `mall_id`가 없으면 아무것도 못 한다. `live`
- ⚠️ **상태가 order가 아니라 item 레벨**이다. 주문 1건 안에서 품목별로 상태가 다르다. `live`
- 상태 코드: `N00` 입금전 / `N10` 상품준비중(=`PAID`) / `N20`·`N21`·`N22` 배송준비 계열(=`PREPARING`) /
  `N30` 배송중 / `N40` 배송완료·`N50` 구매확정 / `C*` 취소 / `R*`·`E*` 반품·교환. `live`
- `R*`/`E*`를 `CANCELLED`로 합치지 않는다. 주문 6상태로 의미가 손실되면 `UNKNOWN`으로 보존. `live`
- 조회 창 3개월 이하, 주문 목록 limit 100. write는 단건 1 / 다건 최대 100, 호출한도 40. `docs`
- 발주확인 상당 전이는 `PUT /api/v2/admin/orders/{order_id}`에 `process_status=prepare`.
  성공 판정은 item이 exact `N20`으로 재조회되는지로 한다. `live`

## 11. 폴백

카페24 관리자 주문 엑셀 수동 인제스트.

## 12. 주문경로(`order_place`) — 한 응답에 여러 지면이 섞인다

`GET /admin/orders` 응답의 `market_id` / `order_place_id` / `order_place_name`은
**그 주문이 어느 지면에서 발생했는지**를 알려준다. 자사몰만 있는 게 아니다.

실제 몰에서 API 응답과 판매자센터를 대조해 확인할 예시:

| `market_id` | `order_place_name` | 정체 | 논리 채널 |
| --- | --- | --- | --- |
| `self` / `mobile` | PC쇼핑몰 / 모바일웹 | 자사몰 직접 | `cafe24` |
| `NCHECKOUT` | 네이버 페이 | 자사몰 **네이버페이 주문형** | `cafe24` |
| `KAKAOPAY` | 톡체크아웃 | 자사몰 **카카오 간편구매** | `cafe24` |
| `kakao` | 카카오톡 스토어 | **마켓플러스 연동 마켓 주문** | `kakao` |

- **자사몰 간편결제(`NCHECKOUT`·`KAKAOPAY`)는 자사몰이다.** 주문서가 카페24 주문장에
  생성되고 카페24 주문관리에서 처리된다. 결제 브랜드가 코드명에 들어갔을 뿐이다.
- **마켓플러스로 연동한 마켓 주문만 별도 논리 채널로 분리한다.** 판별식은
  `market_order_no`가 그 마켓 판매자센터 주문번호와 일치하는지다(SKILL.md "채널 귀속" 절).
- 스마트스토어·G마켓·11번가·무신사·쇼피·카카오톡스토어가 마켓플러스 지원 대상이다.
  **자사몰 연동을 시작할 때 마켓계정관리에 무엇이 연동돼 있는지 먼저 확인**한다.
  그러지 않으면 마켓 주문을 자사몰로 잘못 합산하거나, 직접 API로 이미 수집 중인 채널과
  **중복 적재**할 수 있다.
- 네이버페이 주문형은 스마트스토어 직수집과 **중복이 아니다** — 카페24에만 존재하는 주문이다.
- 정산 대사 관점에서 지면별 정산 주체가 다를 수 있으므로 `order_place` 원값을 `raw`에
  보존한다.
