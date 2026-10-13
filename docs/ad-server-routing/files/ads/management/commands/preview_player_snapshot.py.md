# `ads/management/commands/preview_player_snapshot.py`

원본 소스 경로: `ads/management/commands/preview_player_snapshot.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

[context_projection.read_snapshot_package](../../context_projection.py.md#def-read_snapshot_packagesource-contract_path)로 원본·수신 계약을 대조하고, 최대 첫 한 행만 [normalize_snapshot](../../context_projection.py.md#def-normalize_snapshotrow-media_idvillage-game)으로 정규화해 표준 출력하는 Django 관리 명령이다. 파일 저장·Mongo 반영·광고 선택·CDC 접속을 수행하지 않는다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속하며 옵션 등록과 실행 진입점을 정의한다.
2. **직접 호출:** 클래스 선언 자체의 직접 호출은 없고 Django가 add_arguments와 handle을 호출한다.
3. **반환·상태:** help는 수신 계약 확인과 정규화 첫 행 미리보기를 설명한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source·--contract는 필수, --media-id는 선택 옵션이다. media-id의 기본값은 settings.ADS_MEDIA_ID이며 환경변수 ADS_MEDIA_ID가 없으면 `"village-game"`이다. 별도 type 변환은 없다.
2. **직접 호출:** parser.add_argument를 세 번 호출한다.
3. **반환·상태:** parser를 변경하며 반환값은 없다. media-id는 handle의 media_id 키로 전달한다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** media_id.strip()이 비면 ValueError다. 앞뒤 공백은 검사용으로만 제거하므로 비어 있지 않은 문자열의 원래 값은 유지한다. read_snapshot_package가 계약 JSON 객체·실제 검사 결과·고정 계약 메타데이터·created_at·source_path를 확인하고 재읽기 SHA-256도 대조한다. rows[:1]만 normalize_snapshot에 전달한다. OSError·TypeError·ValueError·KeyError는 원인을 유지한 CommandError로 바꾼다. 직접 호출에서 문자열이 아닌 media_id의 .strip()으로 생긴 AttributeError는 잡지 않는다.
2. **직접 호출:** options["media_id"].strip → [read_snapshot_package](../../context_projection.py.md#def-read_snapshot_packagesource-contract_path) → 최대 한 번의 [normalize_snapshot](../../context_projection.py.md#def-normalize_snapshotrow-media_idvillage-game) → json.dumps(ensure_ascii=False, sort_keys=True, indent=2) → self.stdout.write.
3. **반환·상태:** rows·source_sha256·media_id·input_preview·preview 사전을 2칸 들여쓰기 JSON으로 표준 출력한다. rows는 전체 원본 행 수, source_sha256은 검사한 원본 SHA-256, input_preview는 원본 첫 행을 담은 최대 한 항목의 목록이다. preview는 그 행의 정규화 결과 목록이며 빈 파일이면 두 목록 모두 []다. 명시적 반환값은 없고 출력 직렬화·stdout은 try 바깥이다.

### 정규화 미리보기

preview의 각 결과는 schema_version=`"player-context-change/v1"`·source_kind=`"player-snapshot"`·media_id·문자열 subject_id·op=`"upsert"`·version·event_time·context·change_id를 담는다. event_time과 context.updated_at은 UTC로 정규화한 원본 updated_at이다. context에는 문자열 player_id·room_id·coins·version·updated_at만 포함한다. change_id는 change_id를 붙이기 전 사전의 정렬된 압축 JSON UTF-8 바이트에 대한 SHA-256이다. captured_at은 검사하지만 정규화 출력에 포함하지 않는다.

계약의 artifact_id=`"data/exports/player-cdc.ndjson"`·복수 public_fields 등 고정값은 [read_snapshot_package](../../context_projection.py.md)에 정의된다. 계약 source_path는 비어 있지 않은 문자열이어야 하고 resolve 결과가 --source와 같아야 한다. 기대 필드의 JSON 직렬화 결과를 비교하므로 bool과 숫자의 타입 차이도 거절한다. [write_snapshot_contract](write_snapshot_contract.py.md)의 artifact_id·public_fields 출력은 현재 이 조건과 일치한다. 첫 행 미리보기는 전체 입력을 반영하거나 실행 중인 게임 변경을 관찰한 결과가 아니다.
