# `ads/lake_files.py`

원본 소스 경로: `ads/lake_files.py` · [전체 라우팅](../../README.md)

## 책임과 경계

정규화 변경의 중복 제거 history와 대상별 최대 version의 current를 메모리에서 만든다. 파일·Mongo 쓰기는 없으며 inspect_player_lake와 demo_player_lake가 호출한다. [정규화 계약](context_projection.py.md)을 함께 확인한다.

## `def stable_json(row)`

Signature: `def stable_json(row)`

1. **검증·변환:** JSON 직렬화 가능한 값을 받는다.
2. **직접 호출:** json.dumps(ensure_ascii=False, sort_keys=True, separators=(",", ":")).
3. **반환·상태:** 정렬된 compact JSON 문자열을 반환하며 직렬화 오류를 전파한다.

## `def build_history(rows)`

Signature: `def build_history(rows)`

1. **검증·변환:** player-context-change/v1·upsert/delete·bool 제외 0 이상 int version·dict context·필수 비어 있지 않은 문자열·시간대 있는 event_time을 검사한다. 동일 change_id의 다른 전체 JSON은 거절한다. 전체 정규화 계약이나 change_id 해시를 여기서 대조하지 않는다.
2. **직접 호출:** datetime.fromisoformat → stable_json(중복 비교) → sorted(event_time, change_id).
3. **반환·상태:** 동일 ID·동일 내용은 하나로 합친 시간순 행 목록을 반환한다. 입력 행 사전을 복사하지 않으며 빈 입력은 []다. 파일 소비 명령은 먼저 _read_context_changes로 더 엄격하게 검사한다.

## `def build_current(history)`

Signature: `def build_current(history)`

1. **검증·변환:** build_history 뒤 매체·대상·version·change_id 순으로 정렬한다. make_context_document가 각 행의 전체 계약·해시를 검증한다. 같은 version의 다른 deleted/context는 거절한다.
2. **직접 호출:** build_history → sorted → make_context_document → _id별 후보 비교 → sorted(current).
3. **반환·상태:** 대상별 최대 version을 player-current/v1·공개 문서 형태로 반환한다. 삭제 tombstone도 남기며 낮은 version으로 부활하지 않는다. 같은 version·같은 상태는 먼저 정렬된 후보를 유지한다. 반환 순서는 _id 오름차순이고 빈 입력은 []다.
