# `ads/media_urls.py`

원본 소스 경로: `ads/media_urls.py` · 광고 작업 폴더 기준. [전체 라우팅](../../README.md)

## 책임과 경계

최상위 `api/media/` 뒤에 붙는 매체 전용 선택·사건 경로를 등록한다.

## 호출자와 직접 의존

`ad_config.urls`의 `path("api/media/", include("ads.media_urls"))`.

관련 문서: [ads/views.py](views.py.md), [ad_config/ad_config/urls.py](../ad_config/ad_config/urls.py.md).

## 모듈 실행과 값 계약

`app_name="media_ads"`. `decision/` → `views.decision`, `events/` → `views.event`다. 두 view의 decorator가 POST만 허용한다. 직접 정의한 함수·클래스는 없다. 실제 전체 경로는 `/api/media/decision/`·`/api/media/events/`이며 이 파일 안에 `api/media/`를 다시 붙이지 않는다.
