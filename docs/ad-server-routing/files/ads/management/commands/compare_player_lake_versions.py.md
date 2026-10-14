# `ads/management/commands/compare_player_lake_versions.py`

원본 소스 경로: `ads/management/commands/compare_player_lake_versions.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

보존한 두 Lake 버전의 파일 SHA·행 수를 검증하고 지문을 대조한다.

## `def read_lake_manifest(folder)`

Signature: `def read_lake_manifest(folder)`

1. **검증·변환:** manifest.json의 schema_version=player-lake/v1, history/current 파일명, 파일 바이트 SHA와 splitlines 행 수를 대조한다.
2. **직접 호출:** Path.read_text·json.loads → read_bytes → hashlib.sha256 → len(splitlines).
3. **반환·상태:** manifest 사전을 반환한다. NDJSON 행의 JSON/의미나 원본 파일 SHA를 재검사하지 않으며 최상위 집계 필드와 files 행 수의 상호 일치도 별도로 검사하지 않는다. 파일/JSON/누락 키 오류는 전파한다. 저장하지 않는다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django 관리 명령 로더 → add_arguments·handle.
3. **반환·상태:** 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --before·--after 필수이며 두 버전의 디렉터리 경로다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하고 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** 등록된 옵션을 받아 다음 계약을 적용한다.
2. **직접 호출:** read_lake_manifest(전후) → source_sha256·files 레코드 비교 → json.dumps → stdout.write.
3. **반환·상태:** before·after·source_matches·history_matches·current_matches·전후 input/history/current 행 수를 출력한다. history/current 일치는 파일 레코드 전체(path·rows·sha256)의 == 비교다. created_at이나 source_path는 비교하지 않는다. 차이가 있어도 정상 종료한다. OSError·ValueError·KeyError·TypeError를 CommandError로 바꾸며 저장하지 않는다.
