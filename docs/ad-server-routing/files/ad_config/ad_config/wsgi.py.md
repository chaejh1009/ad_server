# `ad_config/ad_config/wsgi.py`

원본 소스 경로: `ad_config/ad_config/wsgi.py` · 광고 작업 폴더 기준. [전체 라우팅](../../../README.md)

## 책임과 경계

WSGI 서버가 import할 Django `application` 객체를 만든다.

## 호출자와 직접 의존

이 모듈의 `application`을 지정한 WSGI 서버. settings의 `WSGI_APPLICATION`도 이 모듈을 가리킨다.

관련 문서: [ad_config/ad_config/settings.py](settings.py.md), [ad_config/ad_config/urls.py](urls.py.md).

## 모듈 실행과 값 계약

`DJANGO_SETTINGS_MODULE`이 없을 때 `ad_config.settings`로 지정하고 `django.core.wsgi.get_wsgi_application()`을 호출한다. 반환된 WSGI callable을 `application`에 저장한다. 직접 정의한 함수·클래스는 없다.
