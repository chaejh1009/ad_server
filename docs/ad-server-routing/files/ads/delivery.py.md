# `ads/delivery.py`

원본 소스 경로: `ads/delivery.py` · [전체 라우팅](../../README.md)

## 책임과 경계

[deliver_ad_events 명령](management/commands/deliver_ad_events.py.md)이 호출하는 로컬 NDJSON 전달 서비스다. 한 writer가 동일 파일을 관리하는 구조이며 Mongo 사건에 file_delivered_at 표식을 남긴다.

## `def deliver_events(output_path, limit=100)`

Signature: `def deliver_events(output_path, limit=100)`

1. **검증·변환:** limit은 bool을 제외한 양수 int여야 한다. 기존 파일이 있으면 read_ndjson으로 읽어 event_id별로 중복 제거한다. 동일 ID의 다른 내용은 ValueError다. file_delivered_at 필드가 없는 사건을 event_time·event_id 오름차순으로 최대 limit개 읽고 EVENT_FIELDS 공개 12필드로 투영한다. 기존 파일과 새 사건의 동일 ID 내용 충돌도 거절한다.
2. **직접 호출:** Path.exists → read_ndjson → get_db().ad_events.find(...).sort(...).limit(limit) → write_ndjson(파일명.tmp, 정렬한 전체 행) → Path.replace(output_path) → 사건별 update_one({_id}, {$set: {file_delivered_at}}) → count_documents.
3. **반환·상태:** processed(이번 조회 사건 수)·total(전체 사건 수)·pending(표식 없는 사건 수) 사전을 반환한다. 표식은 현재 UTC ISO 문자열이다. 대기 사건이 없어도 파일을 다시 쓰며 기존 파일이 없으면 빈 파일을 만든다. 파일/JSON/Mongo 오류와 필수 필드 누락은 전파한다.

## 재시도와 저장 경계

파일 교체를 마친 뒤 표식을 쓴다. 그 사이 중단되면 다음 실행에서 파일의 같은 ID·내용을 확인하고 표식을 보완할 수 있다. 파일과 Mongo를 하나의 트랜잭션으로 묶지 않으며 여러 writer의 동시 실행을 조정하지 않는다. 표식이 이미 있는 사건은 파일이 사라져도 다시 선택되지 않는다. 전달 파일은 원본 event_time 문자열·event_id로 정렬한다. 보고서 집계나 게시는 수행하지 않는다.
