# `ads/urls.py`

원본 소스 경로: `ads/urls.py` · 광고 작업 폴더 기준. [전체 라우팅](../../README.md)

## 책임과 경계

광고주 HTML 화면과 세션 JSON 관리 API의 앱 상대 경로를 등록한다.

## 호출자와 직접 의존

최상위 URLconf가 빈 접두어와 `api/ads/` 접두어로 각각 include한다.

관련 문서: [ads/views.py](views.py.md), [ads/web_views.py](web_views.py.md), [ad_config/ad_config/urls.py](../ad_config/ad_config/urls.py.md).

## 모듈 실행과 값 계약

`app_name="ads"`. `advertiser/campaigns/` → `web_views.campaign_view`, `advertiser/bids/` → `web_views.bid_view`, `advertiser/events/` → `web_views.event_view`. `advertiser/reports/` → `web_views.report_view` (name="web-reports"). `campaigns/` → `views.campaigns`, `bids/` → `views.bids`. 각 항목은 두 include 접두어에 대해 모두 살아 있다. 직접 정의한 함수·클래스는 없다. export/context 경로는 등록되어 있지 않다.
