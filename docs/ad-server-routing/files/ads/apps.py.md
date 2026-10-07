# `ads/apps.py`

원본 소스 경로: `ads/apps.py` · 광고 작업 폴더 기준. [전체 라우팅](../../README.md)

## 책임과 경계

Django가 광고 앱을 로드할 때 사용하는 앱 메타데이터를 선언한다.

## 호출자와 직접 의존

Django INSTALLED_APPS의 `ads` 앱 로딩.

관련 문서: [ad_config/ad_config/settings.py](../ad_config/ad_config/settings.py.md).

## `AdsConfig`

Signature: `class AdsConfig(AppConfig)` · 소스 4행.

1. **검증·변환:** 별도의 입력 검증이나 사용자 정의 메서드는 없다. `name="ads"`, `default_auto_field="django.db.models.BigAutoField"`를 선언한다.
2. **직접 호출:** 기반 클래스는 Django `AppConfig`다. 이 클래스 본문에는 프로젝트 함수를 호출하는 코드가 없다.
3. **반환·상태:** Django 앱 레지스트리에 앱의 이름과 기본 자동 PK 형식을 제공한다. 상속된 프레임워크 메서드를 이 파일의 구현으로 나열하지 않는다.
