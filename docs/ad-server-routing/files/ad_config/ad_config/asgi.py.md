# `ad_config/ad_config/asgi.py`

원본 소스 경로: `ad_config/ad_config/asgi.py` · 광고 작업 폴더 기준. [전체 라우팅](../../../README.md)

## 책임과 경계

ASGI 서버가 import할 Django `application` 객체를 만든다.

## 호출자와 직접 의존

이 모듈의 `application`을 지정한 ASGI 서버.

관련 문서: [ad_config/ad_config/settings.py](settings.py.md), [ad_config/ad_config/urls.py](urls.py.md).

## 모듈 실행과 값 계약

`DJANGO_SETTINGS_MODULE`을 `setdefault`로 지정하고 `django.core.asgi.get_asgi_application()`을 호출한다. 반환된 ASGI callable을 모듈 변수 `application`으로 노출한다. 이 파일에는 직접 정의한 함수·클래스가 없으며 WebSocket router나 Channels 조립도 없다.
