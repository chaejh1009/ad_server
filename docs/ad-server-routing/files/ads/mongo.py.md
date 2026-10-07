# `ads/mongo.py`

원본 소스 경로: `ads/mongo.py` · 광고 작업 폴더 기준. [전체 라우팅](../../README.md)

## 책임과 경계

한 프로세스의 MongoClient 연결 풀과 설정된 광고 Database 핸들을 제공한다.

## 호출자와 직접 의존

services·repository·events·web_views의 Mongo 접근.

관련 문서: [ad_config/ad_config/settings.py](../ad_config/ad_config/settings.py.md).

## `def get_client()`

Signature: `def get_client()` · 소스 7행.

1. **검증·변환:** 추가 URI 검증이나 ping은 하지 않는다. `lru_cache(maxsize=1)`로 인수 없는 호출 결과를 프로세스 안에서 재사용한다.
2. **직접 호출:** `MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000)`.
3. **반환·상태:** MongoClient를 반환한다. 생성과 DB 핸들 획득만으로 실제 조회 성공을 보장하지 않는다. 종료·cache_clear 호출은 이 모듈에 없다.

## `def get_db()`

Signature: `def get_db()` · 소스 15행.

1. **검증·변환:** 설정의 MONGO_DB 이름을 사용한다. 이름을 변환하거나 별도 유효성 검사를 하지 않는다.
2. **직접 호출:** 이 파일의 `get_client()` 호출 → 클라이언트의 `settings.MONGO_DB` 항목 접근.
3. **반환·상태:** PyMongo Database 핸들을 반환한다. 컬렉션 조회·삽입은 호출자가 수행한다.
