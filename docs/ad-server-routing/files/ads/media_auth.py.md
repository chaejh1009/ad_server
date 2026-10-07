# `ads/media_auth.py`

원본 소스 경로: `ads/media_auth.py` · 광고 작업 폴더 기준. [전체 라우팅](../../README.md)

## 책임과 경계

게임 등 매체 서버의 POST를 두 헤더와 공개 subject로 인증하는 decorator factory다. 광고주 세션·게임 ORM을 읽지 않는다.

## 호출자와 직접 의존

`ads.views.decision`·`ads.views.event`의 decorator.

관련 문서: [ads/services.py](services.py.md), [ad_config/ad_config/settings.py](../ad_config/ad_config/settings.py.md), [ads/views.py](views.py.md).

## `def media_api_methods(*allowed)`

Signature: `def media_api_methods(*allowed)` · 소스 12행.

1. **검증·변환:** 허용 메서드 → X-Media-ID로 MEDIA_KEYS 조회 → X-Media-Key 상수시간 비교 → application/json·JSON 객체 → clean_subject → subject.media_id와 헤더 매체 일치 순서로 검사한다.
2. **직접 호출:** decorator가 반환하는 내부 `wrapped(request, *args, **kwargs)`가 `hmac.compare_digest()`·`json.loads()`·`services.clean_subject()`를 호출한다. 성공하면 `request.subject`와 `request.media_body`를 설정하고 감싼 view를 호출한다. `csrf_exempt`·`wraps`를 적용한다.
3. **반환·상태:** factory는 decorator를 반환한다. 요청은 메서드 오류 405(+Allow), 인증 실패 401 media_auth_required, 입력 오류 400(error 문자열), PyMongoError 503 ads_unavailable 또는 실제 view의 응답으로 끝난다. 메서드 검사가 인증보다 먼저다.
