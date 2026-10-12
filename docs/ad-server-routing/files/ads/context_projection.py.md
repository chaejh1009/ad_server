# `ads/context_projection.py`

원본 소스 경로: `ads/context_projection.py` · [전체 라우팅](../../README.md)

## 책임과 경계

동결된 플레이어 공개 스냅샷과 수신 계약을 소비 직전에 대조하고 공개 행을 player-context-change/v1 사전으로 정규화한다. 현재 호출자는 [preview_player_snapshot 명령](management/commands/preview_player_snapshot.py.md)이다. 이 모듈은 파일을 읽으며 저장·HTTP 응답·Mongo 접근·게임 ORM 접근은 하지 않는다. 미리보기 JSON의 표준 출력은 명령의 책임이다.

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

## 광고 선택과의 현재 연결

명령은 read_snapshot_package로 파일 전체와 계약을 대조한 뒤 원본 순서의 첫 행에만 normalize_snapshot을 호출한다. 전체 행 수·원본 sha256·매체 ID·원본 첫 행·정규화 첫 행을 JSON으로 표준 출력하며 파일을 저장하지 않는다. 빈 파일이면 두 미리보기 목록은 비어 있다. 현재 이 두 함수의 호출은 preview_player_snapshot에만 있으며 [views.decision](views.py.md) → [services.choose_ad](services.py.md) 흐름에 연결되지 않았다. 정규화된 context를 광고 결정·보고서에 자동 주입하거나 중복 change_id를 저장·제거하지 않는다. 정규화한 행의 op는 upsert이며 파일에 없는 ID의 삭제를 추론하지 않는다.
