# `ad_config/ad_config/settings.py`

원본 소스 경로: `ad_config/ad_config/settings.py` · 광고 작업 폴더 기준. [전체 라우팅](../../../README.md)

## 책임과 경계

광고 서버의 경로·환경설정·Django 앱/미들웨어·SQLite 인증 저장소·Mongo 연결 값·정적 파일 검색 위치를 정의한다. 소스 설정의 구조만 기록하며 환경파일과 비밀값은 문서에 포함하지 않는다.

## 호출자와 직접 의존

manage.py, ASGI/WSGI 초기화 및 Django settings 접근.

관련 문서: [ad_config/ad_config/urls.py](urls.py.md), [ad_config/ad_config/wsgi.py](wsgi.py.md), [ads/apps.py](../../ads/apps.py.md), [ads/mongo.py](../../ads/mongo.py.md), [ads/media_auth.py](../../ads/media_auth.py.md).

## 모듈 실행과 값 계약

`BASE_DIR`은 manage.py가 있는 `ad_config/`, `WORKING_DIR`은 광고 작업 폴더다. 바깥 `ads`를 import할 수 있도록 WORKING_DIR을 `sys.path`에 추가한다. 런타임에는 `load_dotenv(WORKING_DIR / ".env", override=True)`를 호출한다. 이번 문서 생성에서는 `.env`를 읽거나 모듈을 import하지 않았다.

필수 환경 이름은 `ADS_SECRET_KEY`, `MONGO_URI`, `ADS_MEDIA_ID`, `ADS_MEDIA_KEY`다. `MONGO_DB` 기본값은 `village_ads`다. `MEDIA_KEYS`는 매체 ID → 공유 키 사전이다. 키 값은 기록하지 않는다. `ADS_BASE_URL`·`ADS_MEDIA_ID`·`ADS_MEDIA_KEY` 설정도 존재하지만 현재 매체 요청을 받는 쪽의 인증은 `MEDIA_KEYS`를 사용한다.

**현재 덮어쓰기:** 앞에서 환경으로 읽은 `SECRET_KEY`가 뒤의 개발용 고정값으로 재설정된다. 앞의 localhost `ALLOWED_HOSTS`도 뒤에서 빈 목록으로 재설정된다. `DEBUG=True`다. 문서는 이 실제 순서를 기록하며 비밀 상수 자체는 복제하지 않는다.

Django 기본 인증·세션·admin·staticfiles와 `ads`를 등록한다. 미들웨어는 Security → Session → Common → CSRF → Authentication → Messages → Clickjacking 순서다. 세션 쿠키 이름은 `ads_sessionid`, CSRF 쿠키 이름은 `ads_csrftoken`이다. 로그인·로그아웃 대상은 `/accounts/login/`, 로그인 뒤에는 `/advertiser/campaigns/`로 간다.

인증·세션 ORM 저장소는 `BASE_DIR / "db.sqlite3"`의 SQLite다. 광고 캠페인·입찰·결정·사건은 `ads.mongo`를 통해 별도 MongoDB를 사용한다. `ROOT_URLCONF`는 `ad_config.urls`, 템플릿은 앱 디렉터리를 검색한다. `TIME_ZONE="UTC"`, `USE_TZ=True`다.

`STATIC_URL="static/"`, `STATICFILES_DIRS=[WORKING_DIR / "ads" / "statics"]`다. 이미지 파일은 이 검색 위치 아래의 `ads/creatives/`에 있다. 직접 정의한 함수·클래스는 없다.
