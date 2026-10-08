# `ads/reporting.py`

원본 소스 경로: `ads/reporting.py` · [전체 라우팅](../../README.md)

## 책임과 경계

ad-event/v1 사건을 서울 노출일 기준 ad-report/v1 보고서로 집계하고 Mongo ad_daily_reports에 게시·조회한다. build_ad_reports·check_ad_reports는 집계, load_ad_reports는 게시, web_views.report_view는 소유자별 조회를 호출한다. SEOUL은 UTC+09:00 고정 오프셋이다.

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

## `def build_daily_reports(events, generated_at=None)`

Signature: `def build_daily_reports(events, generated_at=None)`

1. **검증·변환:** generated_at이 참이면 parse_utc로 정규화하고 아니면 현재 UTC 시각을 사용한다. schema_version=ad-event/v1만 허용한다. 같은 event_id의 같은 내용은 중복 제거하고 다른 내용은 ValueError다. event_id는 decision_id:event_type이어야 한다. impression은 impression_time과 event_time이 같은 순간이어야 한다. click은 같은 입력에 선행 impression이 있어야 하며 subject·campaign_id·owner_user_id·slot_id·bid_amount와 노출 기준 시각이 일치해야 한다.
2. **직접 호출:** parse_utc → impression_time.astimezone(SEOUL).date().isoformat() → (owner_user_id, campaign_id, slot_id, date)별 누적 → json.dumps로 _id 생성 → _id 순 정렬. Mongo나 파일을 직접 읽고 쓰지 않는다.
3. **반환·상태:** ad-report/v1 행 목록을 반환한다. impressions·clicks를 각각 세고 bid_units_sum은 노출의 bid_amount만 더한다. ctr은 clicks/impressions이며 노출 0이면 0.0이다. generated_at은 공통 UTC ISO 시각, source_max_event_time은 그룹의 최대 사건 시각이다. 빈 입력은 빈 목록이다. 알 수 없는 사건 종류는 ValueError이며 필수 키 누락·타입 오류는 전파한다.

## 집계 계약과 제한

클릭은 클릭일이 아니라 서울 기준 노출일에 귀속한다. 입력의 배열 순서와 무관하게 같은 결정의 노출 존재를 검사하지만 클릭 시각이 노출 이후인지까지 비교하지 않는다. bid_amount의 양수·타입 검증이나 subject 스키마 전체 검증은 수행하지 않는다. 업무 키 JSON 형식은 publish_reports와 같다. [build_ad_reports](management/commands/build_ad_reports.py.md)는 후보 파일만 만들고, [load_ad_reports](management/commands/load_ad_reports.py.md)가 별도로 게시한다.
