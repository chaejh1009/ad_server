# `ads/admin.py`

원본 소스 경로: `ads/admin.py` · 광고 작업 폴더 기준. [전체 라우팅](../../README.md)

## 책임과 경계

Django admin 등록을 위한 앱 모듈이다. 현재는 `django.contrib.admin` import와 안내 주석만 있다.

## 호출자와 직접 의존

Django admin autodiscovery.

관련 문서: [ads/models.py](models.py.md), [ad_config/ad_config/urls.py](../ad_config/ad_config/urls.py.md).

## 모듈 실행과 값 계약

직접 정의한 함수·클래스·ModelAdmin·모델 등록 호출은 없다. `/admin/` 경로 자체와 Django 기본 인증 앱의 등록은 최상위 Django 구성에 속한다. 이 파일을 제외하지 않고 현재의 비어 있는 등록 책임을 기록한다.
