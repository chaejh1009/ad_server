# `ads/snapshot_intake.py`

원본 소스 경로: `ads/snapshot_intake.py` · [전체 라우팅](../../README.md)

## 책임과 경계

동결된 플레이어 공개 스냅샷 NDJSON의 필드·타입·출처·수집 시각을 검사하고 CDC 준비 상태·스냅샷 인계 계약·파일 간 상태 비교·누락 요약 결과를 만든다. 교육용 r/u/d 변경 이벤트의 공개 상태도 검증한다. 스냅샷 검사는 [inspect_player_snapshot 명령](management/commands/inspect_player_snapshot.py.md), 준비 상태는 [write_cdc_readiness 명령](management/commands/write_cdc_readiness.py.md)이 호출한다. [handoff_player_snapshot 명령](management/commands/handoff_player_snapshot.py.md)은 원본과 계약을 새 수신 폴더에 인계한다. 스냅샷 검사는 한 번 읽은 바이트로 검증과 SHA-256 계산을 수행하며 준비 상태는 선택 경로의 제공·존재 여부를 기록한다. HTTP 경로·Mongo 저장·게임 ORM 접근은 없다. 스냅샷은 단일 작성자와 사용 완료까지 입력 불변을 전제로 하며 파일 잠금은 제공하지 않는다.

## `def _read_snapshot(path)`

Signature: `def _read_snapshot(path)`

1. **검증·변환:** Path(path).read_bytes로 전체 파일을 한 번 읽고 UTF-8로 해석한다. 각 줄을 json.loads로 읽으며 빈 줄·dict가 아닌 값은 행 번호가 포함된 ValueError다. 빈 파일은 빈 목록이다.
2. **직접 호출:** Path.read_bytes → io.StringIO → enumerate → json.loads → hashlib.sha256(payload).hexdigest.
3. **반환·상태:** (행 목록, 원본 바이트 SHA-256 문자열)을 반환한다. 파일·UTF-8·JSON 오류를 전파하고 저장 상태를 변경하지 않는다.

## `def _check_public_state(row)`

Signature: `def _check_public_state(row)`

1. **검증·변환:** dict의 키가 id·room_id·coins·version·updated_at 다섯 개와 정확히 일치해야 한다. id는 양수 int, room_id는 문자열, coins는 int, version은 0 이상 int여야 한다. 정수 검사에서 bool을 거절한다. 빈 room_id와 음수 coins는 별도로 거절하지 않는다.
2. **직접 호출:** [parse_utc](timestamps.py.md)(row["updated_at"])로 시간대 있는 시각인지 검사한다.
3. **반환·상태:** 정상 반환값은 None이다. 입력을 수정하지 않으며 검증 오류는 ValueError 등으로 전파한다. 파싱한 UTC 시각으로 원본 문자열을 교체하지 않는다.

## `def inspect_snapshot(path)`

Signature: `def inspect_snapshot(path)`

1. **검증·변환:** 모든 행에 공개 다섯 필드와 schema_version·source_kind·captured_at, 정확히 여덟 키를 요구한다. schema_version="player-snapshot/v1", source_kind="player-snapshot"이어야 한다. 공개 상태를 검사하고 같은 id의 재등장은 내용이 같아도 거절한다. captured_at은 시간대 있는 시각이어야 하며 모든 행의 원본 값이 같아야 한다. 같은 순간이라도 다른 문자열 표현이면 다른 수집으로 거절한다.
2. **직접 호출:** _read_snapshot → 각 행의 _check_public_state → parse_utc(captured_at) → sorted(seen).
3. **반환·상태:** rows·public_ids(정렬된 ID 목록)·source_kind·schema_version·captured_at·sha256 사전을 반환한다. 빈 파일도 허용하며 rows=0·public_ids=[]·captured_at=None이다. 오류를 전파하며 파일이나 DB를 수정하지 않는다.

## `def readiness(mysql_config=None, connect_home=None, debezium_dir=None)`

Signature: `def readiness(mysql_config=None, connect_home=None, debezium_dir=None)`

1. **검증·변환:** 세 선택 인수를 mysql_config·connect_home·debezium_dir 키로 모은다. 각 값의 bool로 supplied를 판정하고 값이 참일 때만 Path(value).exists()로 exists를 확인한다. 생략하거나 빈 문자열이면 supplied=False·exists=False다. 경로가 파일인지 디렉터리인지, 설정 내용이 유효한지는 검사하지 않는다. 상대경로는 실행 프로세스의 현재 작업 폴더 기준이다.
2. **직접 호출:** supplied_paths.items → bool → Path(value).exists. MySQL·Kafka Connect·Debezium에 접속하거나 프로세스를 실행하지 않는다.
3. **반환·상태:** schema_version="cdc-readiness/v1"·paths·mysql_binlog="not-verified"·cdc_reader="not-configured"·connect_worker="not-configured"·debezium_connector="not-configured"·player_change_topic="not-configured"·common_input="player-snapshot/v1"·binlog_cdc_observed=False 사전을 반환한다. 경로가 존재해도 이 상태값은 그대로다. 파일이나 DB를 수정하지 않으며 경로 처리 오류를 호출자에게 전파한다.

paths의 각 키는 {supplied: bool, exists: bool} 사전이다. 입력 경로 문자열 자체는 반환하지 않는다. common_input은 모듈의 SCHEMA_VERSION을 사용하며 스냅샷 파일을 읽거나 inspect_snapshot을 호출하지 않는다. JSON 파일 저장과 표준 출력은 write_cdc_readiness 명령의 책임이다.

## 현재 사용 범위

광고 사건 파일과 별개인 플레이어 공개 상태 검사와 CDC 준비 기록이다. [context_projection](context_projection.py.md)은 검사한 원본과 수신 계약을 대조하고 공개 context 변경 사전을 만든다. 소비자는 미리보기·전체 정규화·스냅샷 갱신 명령이며 광고 선택 context나 보고서에 자동 반영하지 않는다. 계정·좌표 등 추가 필드는 정확한 필드 집합 검사로 거절한다. inspect_snapshot은 전용 읽기 함수를 사용하고 load_rows는 검사 후 exporting.read_ndjson으로 파일을 다시 읽는다. 교육 fixture 저장은 exporting.write_ndjson을 재사용한다. 파일 비교에서 누락된 ID는 삭제 사건으로 바꾸지 않는다. 준비 기록의 경로 존재 여부는 실제 binlog·CDC 원문 관찰이나 연결 성공을 뜻하지 않는다.

## `def change_player(event)`

Signature: `def change_player(event)`

1. **검증·변환:** source_kind가 "teaching-fixture"인 이벤트만 받는다. op="r"은 before=None과 dict인 after, op="u"는 유효한 before·after와 같은 id, op="d"는 dict인 before와 after=None을 요구한다. 다른 op는 ValueError다. 공개 상태는 정확한 다섯 필드·타입·시각 검사를 따른다. 이벤트 자체의 추가 키, version 증가나 coins 변화량은 검사하지 않는다.
2. **직접 호출:** event.get → _check_public_state. r/u는 after, d는 before를 선택한다.
3. **반환·상태:** op·player_id·coins·version·deleted 사전을 반환한다. deleted는 d일 때만 True다. 입력이나 게임 상태를 수정하지 않으며 실제 CDC 이벤트를 처리하지 않는다. 비사전 입력이나 u의 잘못된 before/after에서 생기는 AttributeError는 직접 전파될 수 있다.

## `def build_snapshot_contract(source)`

Signature: `def build_snapshot_contract(source)`

1. **검증·변환:** inspect_snapshot(source)의 검사 결과에 인계 메타데이터를 붙인다. artifact_id="data/exports/player-cdc.ndjson", artifact_version="v2", collector="game.export_player_snapshot"는 입력 경로와 무관한 고정값이다.
2. **직접 호출:** inspect_snapshot → str(source) → datetime.now(timezone.utc).isoformat → list(PUBLIC_FIELDS) → contract.update(inspected).
3. **반환·상태:** source_path·created_at·binlog_cdc_status="not-configured"·position_kind="file-line"·kafka_position=None·public_fields와 검사 결과(rows·public_ids·source_kind·schema_version·captured_at·sha256)를 합친 사전이다. public_fields는 복수 키이며 공개 다섯 필드 목록이다. 생성 시각은 실행마다 달라진다. 파일 저장은 [write_snapshot_contract](management/commands/write_snapshot_contract.py.md)가 맡는다. file-line 값에 실제 줄 위치나 Kafka offset이 추가되지는 않는다.

생성 계약은 handoff_snapshot과 [read_snapshot_package](context_projection.py.md)의 artifact_id·public_fields 조건과 일치한다.

## `def load_rows(path)`

Signature: `def load_rows(path)`

1. **검증·변환:** inspect_snapshot으로 파일 전체를 검사한 다음 read_ndjson으로 다시 읽어 id별 사전으로 만든다.
2. **직접 호출:** inspect_snapshot → [exporting.read_ndjson](exporting.py.md) → dict comprehension.
3. **반환·상태:** {id: 원본 행}을 반환한다. 파일을 두 번 읽으므로 검사와 재읽기 사이에도 입력이 동결되어 있어야 한다. 파일 잠금·두 읽기의 체크섬 대조는 없다.

## `def compare(before, after)`

Signature: `def compare(before, after)`

1. **검증·변환:** id별 사전의 공통 ID를 정렬하고 room_id·coins·version·UTC로 파싱한 updated_at 튜플을 비교한다. 시각 표현이 달라도 같은 순간이면 동일하다. captured_at 등 수집 메타데이터는 비교에서 제외한다. 이 함수 자체는 스냅샷 스키마를 검사하지 않는다.
2. **직접 호출:** set 교집합·차집합 → sorted → parse_utc → changed.append.
3. **반환·상태:** changed에는 id·before_version·after_version·before_coins·after_coins를 담는다. room_id나 updated_at만 달라져도 포함되지만 그 필드의 전후 값은 출력하지 않는다. newly_seen은 이후 파일에만 있는 ID, missing_unknown은 이전 파일에만 있는 ID의 정렬된 목록이다. 누락을 삭제로 확정하지 않는다. 입력이나 DB를 변경하지 않는다. [compare_player_snapshots](management/commands/compare_player_snapshots.py.md)가 두 파일을 load_rows로 검사한 뒤 호출한다.

## `def missing_summary(before, after)`

Signature: `def missing_summary(before, after)`

1. **검증·변환:** id별 사전의 키 중 before에만 있는 ID를 정렬한다. 공통 ID의 행 내용이나 이후 파일에만 있는 ID는 비교하지 않는다. 이 함수 자체는 스냅샷 스키마·타입을 검사하지 않는다.
2. **직접 호출:** set(before)·set(after)의 차집합 → sorted.
3. **반환·상태:** {unknown: 정렬된 누락 ID 목록, source_kind: "snapshot-comparison", delete_events: [], delete_inference_allowed: False}를 반환한다. 누락만으로 삭제를 추론하거나 교육 fixture의 d 사건을 만들지 않으며 입력·DB·파일을 변경하지 않는다. [read_snapshot_missing](management/commands/read_snapshot_missing.py.md)이 두 파일을 load_rows로 검사한 뒤 호출한다.

## `def handoff_snapshot(source, contract_path, target)`

Signature: `def handoff_snapshot(source, contract_path, target)`

1. **검증·변환:** 원본과 출력 경로를 Path로 바꾸고 UTF-8 JSON 계약을 읽은 뒤 원본을 inspect_snapshot으로 검사한다. 계약에는 검사 결과 여섯 키와 artifact_id="data/exports/player-cdc.ndjson"·artifact_version="v2"·public_fields=list(PUBLIC_FIELDS)·position_kind="file-line"·kafka_position=None·collector="game.export_player_snapshot"·binlog_cdc_status="not-configured"가 있어야 하며 기대값과 Python ==로 같아야 한다. created_at은 parse_utc로 검사한다. JSON 객체 여부·source_path와 원본 경로의 일치는 별도로 검사하지 않으며 추가 계약 키는 허용한다. 값 비교는 JSON 타입까지 엄격하게 구별하지 않아 일부 정수·실수·bool 값이 같게 취급될 수 있다. 이미 존재하는 target은 거절한다.
2. **직접 호출:** Path → Path(contract_path).read_text → json.loads → inspect_snapshot → 기대 키 반복 비교 → parse_utc → target.exists → target.parent.mkdir → tempfile.mkdtemp → shutil.copyfile → 수신 파일 read_bytes·hashlib.sha256().hexdigest → 계약 write_text → temporary.rename(target). 같은 부모 아래 임시 폴더의 player-cdc.ndjson을 검사 당시 sha256과 대조하고, 기존 계약을 복사해 source_path만 최종 수신 파일 경로로 바꾼 player-cdc-contract.json을 저장한다. 계약 JSON은 ensure_ascii=False·sort_keys=True·indent=2이며 끝에 줄바꿈을 붙인다.
3. **반환·상태:** 두 파일이 준비된 임시 폴더를 target으로 이름 변경한 뒤 rows·sha256·source_kind="player-snapshot"·target 사전을 반환한다. 원본과 원래 계약은 수정하지 않는다. 복사·체크섬 대조·계약 저장·이름 변경 중 예외가 나면 임시 폴더를 shutil.rmtree(ignore_errors=True)로 정리하고 다시 올린다. 출력 부모 폴더는 남을 수 있다. 파일·JSON·시각 오류를 전파하며 계약의 누락된 created_at은 KeyError, 비객체 계약은 TypeError 등으로 끝날 수 있다. 계약 불일치나 기존 target은 ValueError다. 검사 후 원본이 달라져 복사 checksum이 다르면 ValueError로 인계를 거절한다. 파일 잠금이나 실제 CDC 연결은 없다.

인계와 build_snapshot_contract의 artifact_id·공개 필드 키는 일치한다. 수신 후 소비 직전의 JSON 타입·source_path·원본 변경 검사는 [context_projection.read_snapshot_package](context_projection.py.md)의 책임이다.
