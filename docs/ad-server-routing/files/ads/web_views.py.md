# `ads/web_views.py`

원본 소스 경로: `ads/web_views.py` · 광고 작업 폴더 기준. [전체 라우팅](../../README.md)

## 책임과 경계

광고주 세션으로 캠페인·입찰을 편집하고 자신의 최근 결정·사건을 HTML로 읽는다.

## 호출자와 직접 의존

ads.urls의 advertiser/campaigns·bids·events 경로(최상위 두 include 접두어 모두).

관련 문서: [ads/services.py](services.py.md), [ads/mongo.py](mongo.py.md), [ads/urls.py](urls.py.md).

## `def campaign_view(request)`

Signature: `def campaign_view(request)` · 소스 14행.

1. **검증·변환:** GET·POST만 허용한다. POST form에서 제목·이미지·슬롯·체크박스를 읽고 media_id를 village-game으로 고정한다. active는 체크박스 값이 on인지로 만든다.
2. **직접 호출:** POST: services.save_campaign(request.user, form dict). 공통: services.list_campaigns(request.user) → render("ads/campaigns.html", ...).
3. **반환·상태:** HTML과 campaigns/message를 반환한다. 성공 200, ValueError 400, PyMongoError 503이다. 저장 뒤 redirect하지 않고 같은 요청에서 목록을 다시 렌더한다.

## `def bid_view(request)`

Signature: `def bid_view(request)` · 소스 38행.

1. **검증·변환:** GET·POST만 허용한다. POST의 bid_amount 문자열을 strip하고 [0-9]{1,5}와 1~10000 범위로 검사한다. int로 바꾸어 서비스 필드 bid_units로 전달한다.
2. **직접 호출:** POST: services.save_bid(request.user, {campaign_id, bid_units}). 공통: services.list_bids → 각 row에 표시용 bid_amount=row["bid_units"] 추가 → render("ads/bids.html", ...).
3. **반환·상태:** HTML과 bids/message, 200/400/503을 반환한다. save_bid 반환값을 사용하지 않으므로 현재 orders 반환 결함에도 실제 bids 목록을 표시할 수 있다. 화면의 bid_amount와 저장 필드 bid_units의 이름을 구분한다.

## `def event_view(request)`

Signature: `def event_view(request)` · 소스 65행.

1. **검증·변환:** GET만 허용한다. decisions 조회 범위를 owner_user_id=request.user.pk로 제한하고 selected_at 내림차순 최근 30개를 읽는다.
2. **직접 호출:** get_db().decisions.find(...).sort("selected_at", -1).limit(30) → 각 결정의 ad_events.find_one(결정ID:impression)·find_one(결정ID:click) → render("ads/events.html", ...).
3. **반환·상태:** 행에는 decision_id·campaign_id·bid_amount·selected_at·snapshot_ready·impression·click이 있다. 표시값은 chosen 필드가 없으면 campaign_id/bid_units로 fallback한다. 정상 200, PyMongoError 503. snapshot_ready는 chosen_campaign_id의 bool만 확인하므로 events 서비스의 전체 후보 검증과 같지 않다. 소유자 필드 없는 과거 결정은 조회 결과에 들어오지 않는다.

## 실적 화면의 조회 계약

`event_view`는 `ads/events.html`에 `rows`를 전달한다. 각 결정마다 impression과 click 문서를 각각 한 번 조회하므로 최근 결정 수가 N이면 decisions 조회 한 번과 사건 조회 2N번을 수행한다. 최근 30개 제한은 사건 수가 아니라 결정 수에 적용된다.

저장소 오류가 발생하면 `rows=[]`와 `message="광고 실적 저장소에 연결할 수 없습니다."`를 전달하고 503으로 렌더한다. 이 화면은 결정·사건을 읽기만 하며, 방문 자체로 impression이나 click을 기록하지 않는다.

## 현재 구현에서 확인할 점

세 view의 login_required는 /accounts/login/로 redirect한다. HTML POST는 CSRF 미들웨어를 통과해야 한다. 현재 report_view는 없다. events.html의 일별 보고서 링크 `/advertiser/reports/`는 URLconf에 등록되지 않아 404다.
