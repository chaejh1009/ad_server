# `ads/context_projection.py`

원본 소스 경로: `ads/context_projection.py` · [전체 라우팅](../../README.md)

## 책임과 경계

동결된 플레이어 공개 스냅샷과 수신 계약을 소비 직전에 대조하고 공개 행을 player-context-change/v1 사전으로 정규화한다. 미리보기·전체 정규화·컨텍스트 검사/반영·버전 데모 명령이 호출한다. 정규화 파일 저장과 Mongo player_context의 최신 상태 반영·조회도 담당한다. JSON 표준 출력은 각 명령의 책임이다. HTTP·게임 ORM을 직접 호출하지 않는다.

관련 문서: [snapshot_intake](snapshot_intake.py.md), [timestamps](timestamps.py.md).

## `def read_snapshot_package(source, contract_path)`

Signature: `def read_snapshot_package(source, contract_path)`

1. **검증·변환:** 두 경로를 Path로 바꾸고 UTF-8 JSON 계약이 dict인지 검사한다. inspect_snapshot(source)의 여섯 검사 결과와 artifact_id="data/exports/player-cdc.ndjson"·artifact_version="v2"·collector="game.export_player_snapshot"·binlog_cdc_status="not-configured"·position_kind="file-line"·kafka_position=None·public_fields=list(PUBLIC_FIELDS)를 계약에서 요구한다. 각 키의 값을 sort_keys=True인 JSON 직렬화 결과로 비교하므로 Python ==와 달리 bool·정수·실수의 JSON 표현 차이도 거절한다. 추가 계약 키는 허용한다. created_at을 parse_utc로 검사하고 source_path가 비어 있지 않은 문자열이며 resolve한 경로가 실제 source와 같은지 검사한다.
2. **직접 호출:** Path → contract_path.read_text → json.loads → [inspect_snapshot](snapshot_intake.py.md) → 기대 키 반복·json.dumps 비교 → [parse_utc](timestamps.py.md) → Path.resolve → [_read_snapshot](snapshot_intake.py.md). 마지막 재읽기에서 행과 checksum을 같은 바이트로 얻고 검사 당시 sha256과 대조한다.
3. **반환·상태:** (원본 행 목록, 검사 결과 사전)을 반환한다. 행 순서는 NDJSON 원본 순서이며 정렬하지 않는다. 계약 비객체·기대 키 누락/불일치·source_path 누락/경로 불일치·검사 후 checksum 변경은 ValueError다. 파일·UTF-8·JSON·시각·경로 오류도 전파한다. 입력·계약을 수정하지 않으며 파일 잠금은 없다. 검사를 마친 후 다른 바이트로 바뀐 원본을 그대로 소비하지 않는다.

현재 [build_snapshot_contract](snapshot_intake.py.md)는 artifact_id="game_server/data/exports/player-cdc.ndjson"·public_field(단수)를 생성한다. 그 결과를 그대로 이 함수에 전달하면 artifact_id 비교에서 거절된다. 인계와 미리보기의 소비 계약은 artifact_id="data/exports/player-cdc.ndjson"·public_fields(복수)를 요구한다.

## `def normalize_snapshot(row, media_id='village-game')`

Signature: `def normalize_snapshot(row, media_id='village-game')`

1. **검증·변환:** row가 dict이고 공개 다섯 필드(id·room_id·coins·version·updated_at)와 schema_version·source_kind·captured_at, 정확히 여덟 키를 가져야 한다. schema_version="player-snapshot/v1"·source_kind="player-snapshot"을 요구한다. media_id는 strip한 결과가 비어 있지 않은 문자열인지 검사하며 원래 문자열을 그대로 사용한다. 등록된 매체인지 검사하지 않는다. 공개 다섯 필드를 _check_public_state에 전달하므로 bool을 제외한 양수 int id·문자열 room_id·int coins·0 이상 int version·시간대 있는 updated_at이 필요하다. captured_at도 parse_utc로 검사한다. 한 행만 검사하며 파일 전체의 중복 ID·동일 captured_at 여부는 검사하지 않는다.
2. **직접 호출:** [_check_public_state](snapshot_intake.py.md) → [parse_utc](timestamps.py.md)(captured_at) → str(id) → parse_utc(updated_at).isoformat → context와 change 사전 구성 → json.dumps(ensure_ascii=False, sort_keys=True, separators=(",", ":")) → UTF-8 encode → hashlib.sha256().hexdigest. change_id를 넣기 전 change 사전의 정렬된 compact JSON을 해시한다.
3. **반환·상태:** schema_version="player-context-change/v1"·source_kind="player-snapshot"·media_id·subject_id=str(id)·op="upsert"·version·event_time·context·change_id를 가진 새 사전을 반환한다. context는 player_id=str(id)·room_id·coins·version·updated_at이며 event_time과 context.updated_at은 같은 UTC ISO 문자열이다. captured_at과 입력 schema_version은 출력에 남기지 않는다. 같은 정규화 값은 같은 change_id를 만들며 captured_at만 바뀌거나 updated_at이 같은 순간의 다른 시간대 표현이면 해시는 같다. 입력을 수정하거나 DB·파일에 저장하지 않는다. 검증·시각 오류를 전파한다.


## `def normalize_snapshot_file(source, contract_path, output, media_id='village-game')`

Signature: `def normalize_snapshot_file(source, contract_path, output, media_id='village-game')`

1. **검증·변환:** media_id는 비어 있지 않은 문자열이다. 출력 resolve 경로가 원본/계약과 같으면 거절한다. read_snapshot_package로 전체 입력을 확인한 뒤 모든 행을 정규화하고 change_id 중복을 거절한다.
2. **직접 호출:** Path.resolve → read_snapshot_package → normalize_snapshot(모든 행) → 부모 mkdir → tempfile.TemporaryDirectory → write_ndjson → os.replace.
3. **반환·상태:** 완성한 임시 파일로 출력 NDJSON을 교체한다. path·rows·sha256·schema_version·source_kind·source_sha256·media_id·op_counts={upsert:행수}·unique_change_ids·preview=첫 행 목록을 반환한다. 빈 입력도 저장한다. 변환 실패 시 기존 출력은 유지한다. 파일/검증 오류는 전파하며 파일 잠금은 없다. normalize_snapshot은 콜론 포함 media_id를 거절하지 않지만 이후 Mongo용 키 검증은 거절한다.

## `def context_subject_key(media_id, subject_id)`

Signature: `def context_subject_key(media_id, subject_id)`

1. **검증·변환:** 두 ID가 문자열이고 strip 결과가 비어 있지 않으며 콜론을 포함하지 않아야 한다.
2. **직접 호출:** isinstance·strip 검사.
3. **반환·상태:** 원래 문자열의 media_id + ":" + subject_id를 반환한다. 앞뒤 공백을 제거하지 않는다. 검증 실패는 ValueError다.

## `def _check_context_change(change)`

Signature: `def _check_context_change(change)`

1. **검증·변환:** 정확한 9필드의 dict, player-context-change/v1, player-snapshot 또는 teaching-fixture, upsert 또는 delete를 요구한다. snapshot subject는 앞자리 0 없는 양의 ASCII 십진 문자열이며 upsert만 허용한다. fixture subject는 fixture- 뒤에 내용이 있어야 한다. version은 bool 제외 0 이상 int다.
2. **직접 호출:** context_subject_key → parse_utc(event_time) → 공개 context 검사 → parse_utc(updated_at) → change_id 제외 정렬 compact JSON의 SHA-256 대조.
3. **반환·상태:** event_time은 parse_utc(...).isoformat()과 정확히 같아야 한다. delete context는 {}다. upsert는 player_id·room_id·coins·version·updated_at 정확한 5필드이며 subject/version/event_time과 일치해야 한다. room_id는 str, coins는 bool 제외 int다. change_id 불일치를 거절한다. 반환값/저장은 없으며 검증·시각 오류를 전파한다.

## `def make_context_document(change)`

Signature: `def make_context_document(change)`

1. **검증·변환:** _check_context_change로 전체 계약을 검증한다.
2. **직접 호출:** _check_context_change → context_subject_key → 필드 사전 구성·dict(context).
3. **반환·상태:** media_id·subject_id·version·source_kind·change_id·event_time 및 _id·deleted·context의 9필드 문서를 반환한다. _id는 매체:대상, deleted는 op=="delete"다. 현재 context 분기의 문자열은 "deleted"지만 허용 op에는 없으므로 항상 입력 context를 복사한다. delete 입력은 검증에서 이미 {}로 제한되어 결과도 {}다. 저장하지 않는다.

## `def apply_context(change)`

Signature: `def apply_context(change)`

1. **검증·변환:** make_context_document로 검증 후 최신 version과 비교한다. 같은 version에서는 deleted와 context만 비교하며 change_id·source_kind·event_time을 별도로 비교하지 않는다.
2. **직접 호출:** make_context_document → get_db().player_context → 최대 3회 find_one → insert_one 또는 replace_one({_id, version:읽은 버전}, document).
3. **반환·상태:** 신규/더 큰 version 반영 시 applied, 낮은 version은 stale, 동일 version·동일 상태는 duplicate를 반환한다. 동일 version·다른 상태는 version_conflict ValueError다. 신규 insert의 DuplicateKeyError와 교체 matched_count=0은 재조회한다. 3회 실패는 concurrent_update ValueError다. delete는 물리 삭제 대신 tombstone으로 남겨 오래된 입력의 부활을 막는다. Mongo 오류는 전파한다. 이 함수는 인덱스를 생성하지 않는다.

## `def get_context(media_id, subject_id)`

Signature: `def get_context(media_id, subject_id)`

1. **검증·변환:** context_subject_key로 식별자를 검사한다.
2. **직접 호출:** context_subject_key → get_db().player_context.find_one({_id:key}) → dict(context).
3. **반환·상태:** 문서가 있고 deleted=False면 context의 얕은 복사, 없거나 삭제 표시 상태면 {}를 반환한다. 저장하지 않으며 Mongo/저장 문서 필드 오류를 전파한다.

## 광고 선택과의 현재 연결

미리보기는 첫 행만 표준 출력하고 전체 정규화 명령은 모든 행을 파일로 저장한다. 반영 명령은 선택한 한 행을 player_context에 저장한다. 검사 명령은 고유 인덱스 생성과 조회를 수행하며 데모는 fixture subject를 실제 저장한다. 현재 [views.decision](views.py.md) → [services.choose_ad](services.py.md)는 get_context를 호출하지 않아 이 저장 상태를 광고 선택에 자동 주입하지 않는다. 스냅샷은 upsert만 만들며 누락 ID를 삭제로 추론하지 않는다.
