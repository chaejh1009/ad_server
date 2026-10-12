# `ads/management/commands/write_snapshot_contract.py`

원본 소스 경로: `ads/management/commands/write_snapshot_contract.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

검사한 공개 스냅샷의 행 수·ID·체크섬과 인계 메타데이터를 JSON 파일과 표준 출력으로 기록한다. 원본은 동결 입력을 전제로 한다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속하며 옵션 등록과 실행 진입점을 정의한다.
2. **직접 호출:** 클래스 선언 자체의 직접 호출은 없고 Django가 add_arguments와 handle을 호출한다.
3. **반환·상태:** help는 검사한 파일의 행 수·ID·체크섬을 인계 계약으로 저장함을 설명한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source·--output을 모두 필수 옵션으로 등록한다. 별도 type 변환은 없다.
2. **직접 호출:** parser.add_argument를 두 번 호출한다.
3. **반환·상태:** parser를 변경하며 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** build_snapshot_contract(source)로 검사·계약 생성을 수행한 뒤 출력과 입력의 resolve 결과가 같으면 ValueError다. resolve 비교는 서로 다른 경로의 hard link까지 식별하지 않는다.
2. **직접 호출:** [build_snapshot_contract](../../snapshot_intake.py.md) → Path.resolve → target.parent.mkdir(parents=True, exist_ok=True) → json.dumps(ensure_ascii=False, sort_keys=True, indent=2) → target.write_text(encoding="utf-8") → self.stdout.write.
3. **반환·상태:** 계약 JSON을 2칸 들여쓰기와 마지막 개행으로 덮어쓰고 같은 결과를 들여쓰기 JSON으로 표준 출력한다. artifact_id·collector는 고정값이며 실제 binlog/CDC 검증을 뜻하지 않는다. OSError·ValueError·TypeError·KeyError는 원인을 유지한 CommandError로 바꾸며 stdout 쓰기는 try 바깥이다. 파일 교체는 원자적이지 않다. 명시적 반환값은 없다.

### JSON 출력 계약

| 필드 | 값·조건 |
| --- | --- |
| artifact_id | `"game_server/data/exports/player-cdc.ndjson"` 고정값 |
| artifact_version | `"v2"` |
| source_path | 입력 source를 문자열로 표현한 값. resolve 결과로 바꾸지 않는다. |
| created_at | 실행 시점의 UTC 시각을 ISO 형식으로 표현한 값 |
| collector | `"game.export_player_snapshot"` 고정값 |
| binlog_cdc_status | `"not-configured"` |
| position_kind | `"file-line"`. 실제 줄 위치는 추가하지 않는다. |
| kafka_position | `null` |
| public_field | `id`·`room_id`·`coins`·`version`·`updated_at` 목록. 키가 단수다. |
| rows·public_ids·source_kind·schema_version·captured_at·sha256 | [inspect_snapshot](../../snapshot_intake.py.md)의 실제 검사 결과. source_kind는 `"player-snapshot"`, schema_version은 `"player-snapshot/v1"`이다. 빈 파일은 rows=0·public_ids=[]·captured_at=null이다. |

현재 [handoff_player_snapshot](handoff_player_snapshot.py.md)과 [preview_player_snapshot](preview_player_snapshot.py.md)의 소비 서비스는 artifact_id=`"data/exports/player-cdc.ndjson"`와 복수 키 public_fields를 요구한다. 이 명령이 생성한 계약은 그 조건과 달라 두 명령에 그대로 입력하면 거절된다. 입력 경로를 바꾸어도 artifact_id와 키 이름은 바뀌지 않는다.
