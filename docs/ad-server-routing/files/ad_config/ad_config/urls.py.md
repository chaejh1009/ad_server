# `ad_config/ad_config/urls.py`

원본 소스 경로: `ad_config/ad_config/urls.py` · 광고 작업 폴더 기준. [전체 라우팅](../../../README.md)

## 책임과 경계

광고 서버의 최상위 URL 접두어와 Django 인증·admin view를 연결한다.

## 호출자와 직접 의존

Django URL resolver. `ROOT_URLCONF="ad_config.urls"`.

관련 문서: [ads/auth_views.py](../../ads/auth_views.py.md), [ads/urls.py](../../ads/urls.py.md), [ads/media_urls.py](../../ads/media_urls.py.md).

## 모듈 실행과 값 계약

`admin/`은 Django admin, `api/auth/csrf/·login/·logout/`은 `ads.auth_views`에 연결한다. `accounts/login/·logout/`은 Django `LoginView.as_view()`·`LogoutView.as_view()`에 연결한다.

`ads.urls`를 빈 접두어와 `api/ads/` 접두어에 두 번 포함한다. 따라서 광고주 웹과 캠페인·입찰 API에 두 경로가 실제로 생긴다. 동일한 `app_name="ads"` namespace도 중복된다. `api/media/`는 별도로 `ads.media_urls`에 연결한다. 전체 HTTP 경로는 상위 README의 표를 기준으로 읽는다. 빈 접두어 include는 홈페이지 view를 추가하지 않으므로 `/` 자체에 대응하는 별도 view는 없다.

직접 정의한 함수·클래스는 없으며 `urlpatterns`가 모듈의 호출 계약이다.
