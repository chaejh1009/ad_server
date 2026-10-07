# `ads/reporting.py`

원본 소스 경로: `ads/reporting.py` · [전체 라우팅](../../README.md)

## 책임과 경계

ad-report/v1 보고서 행을 Mongo ad_daily_reports에 게시하고 소유자별로 조회하는 서비스다. 현재 HTTP view·URL이나 게시 명령이 연결되어 있지 않다. SEOUL은 UTC+09:00 고정 오프셋이며 현재 함수에서 사용하지 않는다.

## `def publish_reports(rows)`

Signature: `def publish_reports(rows)`

1. **검증·변환:** 각 행의 schema_version이 ad-report/v1인지 검사한다. (owner_user_id, campaign_id, slot_id, date)를 ensure_ascii=False, separators=(",", ":")인 JSON 배열 문자열로 만들고 _id와 같은지 확인한다. 불일치는 ValueError다.
2. **직접 호출:** json.dumps → get_db().ad_daily_reports.replace_one({_id: row["_id"]}, row, upsert=True).
3. **반환·상태:** 처리한 행 수를 반환한다. 같은 업무 키의 문서는 전체 교체한다. 나머지 필드의 타입·집계값 검증은 없고 필수 키 누락은 KeyError다. 행별 저장이므로 뒤 행 실패 시 앞서 게시한 행은 남는다.

## `def list_reports(owner_user_id)`

Signature: `def list_reports(owner_user_id)`

1. **검증·변환:** 전달된 owner_user_id로 조회 범위를 정한다. 인증·소유자 값 검증은 호출자의 책임이다.
2. **직접 호출:** get_db().ad_daily_reports.find({owner_user_id}, {_id: 0}).sort(date 내림차순, campaign_id·slot_id 오름차순) → list.
3. **반환·상태:** _id가 제외된 보고서 목록을 반환한다. 저장 상태는 변경하지 않는다.

## 현재 구현에서 확인할 점

build_daily_reports는 정의되어 있지 않다. [build_ad_reports 명령](management/commands/build_ad_reports.py.md)은 이 함수를 import하므로 현재 ImportError로 로딩되지 않는다. 일별 집계·보고서 화면까지 구현되었다고 해석하면 안 된다.
