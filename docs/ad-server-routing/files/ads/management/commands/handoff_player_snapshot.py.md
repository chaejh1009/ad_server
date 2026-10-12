# `ads/management/commands/handoff_player_snapshot.py`

원본 소스 경로: `ads/management/commands/handoff_player_snapshot.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

동결된 공개 스냅샷과 계약을 [snapshot_intake.handoff_snapshot](../../snapshot_intake.py.md#def-handoff_snapshotsource-contract_path-target)에 전달해 새 수신 폴더로 인계하는 Django 관리 명령이다. 검증·임시 폴더 작성·최종 폴더 이동은 서비스가 맡는다. DB·Mongo·CDC 연결은 없다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속하며 옵션 등록과 실행 진입점을 정의한다.
2. **직접 호출:** 클래스 선언 자체의 직접 호출은 없고 Django가 add_arguments와 handle을 호출한다.
3. **반환·상태:** help는 검증한 원본과 계약을 새 수신 폴더에 함께 인계함을 설명한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source·--contract·--target을 모두 필수 옵션으로 등록한다. 별도 type 변환은 없다.
2. **직접 호출:** parser.add_argument를 세 번 호출한다.
3. **반환·상태:** parser를 변경하며 반환값은 없다. target은 결과 JSON 파일이 아니라 새 수신 폴더 경로다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** 세 필수 경로를 handoff_snapshot에 전달한다. 서비스가 원본을 inspect_snapshot으로 검사하고 계약 기대 필드·created_at을 확인한다. target이 이미 존재하면 디렉터리·파일 모두 거절한다. OSError·ValueError·TypeError·KeyError는 원인 예외를 유지한 CommandError로 바꾼다.
2. **직접 호출:** [handoff_snapshot](../../snapshot_intake.py.md#def-handoff_snapshotsource-contract_path-target) → json.dumps(ensure_ascii=False, sort_keys=True, indent=2) → self.stdout.write.
3. **반환·상태:** rows·sha256·source_kind=`"player-snapshot"`·target 사전을 2칸 들여쓰기 JSON으로 표준 출력한다. 명시적 반환값은 없다. 서비스는 target 부모 폴더 아래 임시 폴더에 player-cdc.ndjson과 player-cdc-contract.json을 작성하고, 복사 파일 SHA-256 대조 후 임시 폴더를 target으로 rename한다. 계약의 source_path만 최종 수신 파일 경로로 바꾸며 그 외 키는 유지한다. 임시 폴더 처리 실패 시 정리 후 예외를 다시 던진다. stdout 출력은 try 바깥이어서 출력 실패가 CommandError로 바뀌지 않고 이미 인계한 폴더는 남는다.

## 계약·경로 조건

계약은 실제 검사 결과 rows·public_ids·source_kind·schema_version·captured_at·sha256과 일치해야 한다. 추가 기대값은 artifact_id=`"data/exports/player-cdc.ndjson"`·artifact_version=`"v2"`·collector=`"game.export_player_snapshot"`·binlog_cdc_status=`"not-configured"`·position_kind=`"file-line"`·kafka_position=null·public_fields=`["id", "room_id", "coins", "version", "updated_at"]`다. created_at은 시간대 있는 시각이어야 한다.

현재 서비스는 계약을 별도로 dict 검증하지 않고 각 기대값을 Python의 `!=`로 비교한다. JSON 직렬화에 의한 타입 구분은 없으므로 숫자 0/1과 bool처럼 Python에서 같은 값으로 비교되는 경우를 구분하지 않는다. 기존 계약 source_path의 존재나 source 경로 일치는 확인하지 않고 최종 수신 경로로 덮어쓴다. 소비 직전 [preview_player_snapshot](preview_player_snapshot.py.md)이 사용하는 read_snapshot_package는 이와 달리 JSON 값·타입과 source_path를 검사한다.

[write_snapshot_contract](write_snapshot_contract.py.md)는 다른 artifact_id 접두사와 단수 public_field를 생성하므로 그 출력은 이 명령의 계약 조건을 그대로 만족하지 않는다. 원본은 검사부터 복사까지 동결되어 있어야 하며 복사 후 체크섬 불일치는 거절한다. 폴더 존재 검사와 rename 사이의 동시 작성은 잠금으로 제어하지 않으므로 단일 작성자를 전제로 한다. 인계 성공도 실제 binlog·CDC 관찰 증거를 만들지는 않는다.
