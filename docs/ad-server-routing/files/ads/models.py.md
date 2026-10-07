# `ads/models.py`

원본 소스 경로: `ads/models.py` · 광고 작업 폴더 기준. [전체 라우팅](../../README.md)

## 책임과 경계

광고 앱의 Django ORM 모델 정의 위치다. 현재는 `django.db.models` import와 안내 주석만 있다.

## 호출자와 직접 의존

Django 앱의 모델 로딩.

관련 문서: [ads/apps.py](apps.py.md), [ads/mongo.py](mongo.py.md).

## 모듈 실행과 값 계약

직접 정의한 모델·함수·클래스는 없다. 광고 Mongo 컬렉션은 Django 모델로 정의되어 있지 않으며 repository·services·events가 PyMongo로 접근한다. 광고주 User·Session은 Django 기본 인증/세션 모델과 SQLite 설정을 사용한다.
