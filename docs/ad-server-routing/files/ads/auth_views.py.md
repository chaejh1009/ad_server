# `ads/auth_views.py`

원본 소스 경로: `ads/auth_views.py` · 광고 작업 폴더 기준. [전체 라우팅](../../README.md)

## 책임과 경계

JSON 클라이언트용 CSRF 토큰·로그인·로그아웃을 제공한다. 광고 관리·매체 인증과 별도 경계다.

## 호출자와 직접 의존

최상위 `api/auth/` 세 경로.

관련 문서: [ad_config/ad_config/settings.py](../ad_config/ad_config/settings.py.md).

## `def csrf_token(request)`

Signature: `def csrf_token(request)` · 소스 11행.

1. **검증·변환:** `require_GET`으로 GET만 허용한다. `ensure_csrf_cookie`로 CSRF 쿠키 발급 흐름을 적용한다.
2. **직접 호출:** Django `get_token(request)` → `JsonResponse`.
3. **반환·상태:** 200 JSON `{"csrfToken": token}`을 반환한다. 토큰·쿠키의 실제 값은 문서나 로그에 기록하지 않는다.

## `def login_view(request)`

Signature: `def login_view(request)` · 소스 16행.

1. **검증·변환:** `require_POST`. body가 JSON 객체인지, username·password가 문자열인지 검사한다. JSON 오류·비객체는 `400 invalid_json`, 문자열이 아니면 `400 missing_credentials`다.
2. **직접 호출:** `json.loads(request.body)` → Django `authenticate(request, username=..., password=...)` → 성공 시 `login(request, user)`.
3. **반환·상태:** 인증 실패는 401 `{"authenticated": False}`, 성공은 세션을 만든 뒤 200 `{"authenticated": True}`다. 미들웨어의 CSRF 실패는 view 진입 전에 처리된다.

## `def logout_view(request)`

Signature: `def logout_view(request)` · 소스 34행.

1. **검증·변환:** `require_POST`로 POST만 허용한다. 추가 body 검증이나 로그인 필수 guard는 없다.
2. **직접 호출:** Django `logout(request)` → `JsonResponse`.
3. **반환·상태:** 현재 세션을 로그아웃하고 200 `{"authenticated": False}`를 반환한다.

## 현재 구현에서 확인할 점

세 view는 CSRF 면제 대상이 아니다. POST는 settings의 CSRF 미들웨어를 통과해야 한다. JSON 로그인은 Content-Type을 별도로 검사하지 않고 `request.body`를 해석한다. Django form 로그인 `/accounts/login/`은 이 파일의 login_view가 아니다.
