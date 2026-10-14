# `ads/management/commands/inspect_player_lake.py`

원본 소스 경로: `ads/management/commands/inspect_player_lake.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

고정 정규화 파일에서 history/current를 저장 없이 미리 본다. [Lake 함수](../../lake_files.py.md)와 [입력 검사](../../context_projection.py.md)를 호출한다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django 관리 명령 로더 → add_arguments·handle.
3. **반환·상태:** 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source 필수, --manifest 선택, --stage history/current(기본 history), --repeat int(기본 1), --reverse 플래그를 등록한다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하고 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** 등록된 옵션을 받아 아래 계약을 적용한다.
2. **직접 호출:** _read_context_changes → 선택 manifest JSON·_read_context_checkpoint → 반복/역순 → build_history → 선택 build_current → stable_json·SHA-256 → stdout.write.
3. **반환·상태:** repeat는 양수여야 한다. manifest 제공 시 input_sha256·input_rows·input_schema_version·source_kind=player-snapshot, 각 행의 매체/출처 및 checkpoint_path의 완료 위치를 검사한다. manifest의 context 파일·해시나 input_path는 검사하지 않는다. 원본/공급/history/결과 행 수·결과 배열의 JSON SHA·첫 행 preview·written=False를 출력한다. OSError·ValueError·TypeError·KeyError를 CommandError로 바꾼다. 파일·DB를 수정하지 않는다.
