# `ads/exporting.py`

원본 소스 경로: `ads/exporting.py` · [전체 라우팅](../../README.md)

## 책임과 경계

Mongo의 ad_events를 공개 필드만 갖는 NDJSON으로 내보내고, NDJSON 읽기·쓰기와 SHA-256 계산을 제공한다. HTTP 경로는 없다. [export_ad_events 명령](management/commands/export_ad_events.py.md)이 내보내기를 호출한다. [delivery](delivery.py.md)는 공개 필드와 읽기·쓰기를 재사용하고, build_ad_reports·load_ad_reports·check_ad_reports는 NDJSON 유틸리티를 사용한다.

## `def read_ndjson(path)`

Signature: `def read_ndjson(path)`

1. **검증·변환:** UTF-8 파일의 각 줄을 json.loads로 읽는다. 빈 줄이나 dict가 아닌 값은 행 번호를 포함한 ValueError다. 빈 파일은 빈 목록이다.
2. **직접 호출:** Path(path).open → enumerate → json.loads.
3. **반환·상태:** dict 목록을 반환한다. 스키마 검증은 하지 않으며 파일·JSON 오류를 전파한다.

## `def write_ndjson(path, rows)`

Signature: `def write_ndjson(path, rows)`

1. **검증·변환:** 부모 디렉터리를 만들고 ensure_ascii=False, sort_keys=True로 각 행을 직렬화한다.
2. **직접 호출:** Path → mkdir(parents=True, exist_ok=True) → open("w") → json.dumps → hashlib.sha256(target.read_bytes()).hexdigest().
3. **반환·상태:** UTF-8·LF NDJSON 파일을 덮어쓰고 파일 바이트의 SHA-256 문자열을 반환한다. 원자적 파일 교체가 아니며 중간 실패 시 부분 파일이 남을 수 있다.

## `def export_ad_events(output_path, since=None, until=None)`

Signature: `def export_ad_events(output_path, since=None, until=None)`

1. **검증·변환:** 경계 시각은 [parse_utc](timestamps.py.md)로 파싱한다. 두 경계가 있으면 since < until이어야 한다. 각 사건의 impression_time을 UTC로 변환해 [since, until)로 필터링한다. 클릭도 원래 노출 시각 기준으로 포함한다.
2. **직접 호출:** get_db().ad_events.find().sort(event_time, event_id) → parse_utc → EVENT_FIELDS 투영 → rows.sort(event_time, event_id) → write_ndjson.
3. **반환·상태:** path·rows·sha256·schema_version="ad-event/v1"·source_kind="ad-events"·정규화된 since/until을 반환한다. _id는 제외한다. EVENT_FIELDS는 schema_version, event_id, decision_id, event_type, event_time, impression_time, media_id, subject, slot_id, campaign_id, owner_user_id, bid_amount다. 필수 필드 누락은 KeyError이며 별도 복구하지 않는다.

## 호출 계약과 제한

시간 범위는 Mongo 쿼리에서 제한하지 않고 전체 사건을 읽은 뒤 메모리에서 필터링한다. 최종 정렬 키는 UTC로 파싱한 값이 아니라 원본 event_time 문자열과 event_id다. [events](events.py.md)가 저장하는 UTC 문자열을 전제로 한다. 반환 메타데이터는 명령의 표준 출력이며 별도 manifest 파일을 만들지 않는다. 이 모듈은 보고서 집계나 게시를 수행하지 않는다.
