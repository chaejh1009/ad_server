# `ads/views.py`

원본 소스 경로: `ads/views.py` · 광고 작업 폴더 기준. [전체 라우팅](../../README.md)

## 책임과 경계

광고주 세션 JSON API와 매체 서버 JSON API를 서비스 함수에 연결한다. HTML 화면은 web_views가 담당한다.

## 호출자와 직접 의존

ads.urls의 campaigns/bids, ads.media_urls의 decision/events.

관련 문서: [ads/services.py](services.py.md), [ads/events.py](events.py.md), [ads/media_auth.py](media_auth.py.md), [ads/repository.py](repository.py.md).

## `def api_methods(*allowed)`

Signature: `def api_methods(*allowed)` · 소스 13행.

1. **검증·변환:** 내부 wrapper가 광고주 세션 인증 → 허용 HTTP 메서드 순서로 확인한다. 인증되지 않으면 메서드와 관계없이 401이다.
2. **직접 호출:** `wraps(view)`를 적용한 내부 `wrapped(request, *args, **kwargs)` → 인증·메서드 검사 후 원래 view.
3. **반환·상태:** factory는 decorator를 반환한다. 요청은 login_required 401, method_not_allowed 405(+Allow), ValueError 400, PyMongoError 503 또는 view 응답으로 끝난다. TypeError·KeyError는 이 wrapper의 처리 대상이 아니다. CSRF 면제를 적용하지 않는다.

## `def read_json(request)`

Signature: `def read_json(request)` · 소스 34행.

1. **검증·변환:** Content-Type이 application/json인지 검사하고 body가 JSON 객체인지 확인한다.
2. **직접 호출:** `json.loads(request.body)`; JSON/문자 디코딩 오류는 ValueError("invalid JSON")로 변환.
3. **반환·상태:** 검증된 dict를 반환한다. 잘못된 Content-Type·비객체 본문은 ValueError로 호출자에 전달한다.

## `def campaigns(request)`

Signature: `def campaigns(request)` · 소스 48행.

1. **검증·변환:** api_methods("GET", "POST")로 보호된다. GET과 POST를 request.method로 나눈다. POST 본문은 read_json을 거친다.
2. **직접 호출:** GET: services.list_campaigns(request.user). POST: read_json → services.save_campaign(request.user, data).
3. **반환·상태:** GET은 200 {rows:[...]}이고 POST는 저장된 캠페인 dict를 200 JSON으로 반환한다. 서비스 입력·저장소 오류는 decorator가 처리한다.

## `def bids(request)`

Signature: `def bids(request)` · 소스 58행.

1. **검증·변환:** api_methods("GET", "POST")로 보호된다. POST는 read_json으로 객체를 읽는다.
2. **직접 호출:** GET: services.list_bids(request.user). POST: read_json → services.save_bid(request.user, data).
3. **반환·상태:** GET은 200 {rows:[...]}. POST는 저장 함수의 반환을 그대로 JsonResponse(..., status=200)에 넣는다. 현재 repository가 orders를 반환하므로 반환이 None이면 정상 JSON 응답 대신 TypeError가 발생할 수 있다. 쓰기 성공과 HTTP 응답 성공을 구별해야 한다.

## `def decision(request)`

Signature: `def decision(request)` · 소스 68행.

1. **검증·변환:** media_api_methods("POST")가 인증·JSON·subject를 먼저 검사한다. slot_id와 context는 request.media_body에서 읽고 서비스에서 추가 검증한다.
2. **직접 호출:** services.choose_ad(request.subject, request.media_body.get("slot_id"), request.media_body.get("context")) → JsonResponse.
3. **반환·상태:** 선택 결과 또는 빈 광고를 200 JSON으로 반환한다. 성공 응답에는 Cache-Control: no-store를 넣는다. 선택됐다는 사실만으로 노출 사건을 만들지 않는다.

## `def event(request)`

Signature: `def event(request)` · 소스 79행.

1. **검증·변환:** media_api_methods("POST")로 보호된다. 인증된 request.subject와 본문의 decision_id·event_type을 사용한다.
2. **직접 호출:** record_ad_event(request.subject, body.get("decision_id"), body.get("event_type")) → JsonResponse.
3. **반환·상태:** 200 JSON event_id·event_type·created를 반환하고 성공 응답에 Cache-Control: no-store를 붙인다. 오류는 매체 decorator가 400/503으로 변환한다.
