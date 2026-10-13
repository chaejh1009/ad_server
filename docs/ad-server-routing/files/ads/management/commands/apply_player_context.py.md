# `ads/management/commands/apply_player_context.py`

원본 소스 경로: `ads/management/commands/apply_player_context.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

정규화 파일 전체를 사전 검증하고 선택한 한 행을 Mongo player_context에 반영한다. [context_projection](../../context_projection.py.md)의 버전 비교 정책을 사용한다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django가 옵션 등록과 handle을 호출한다.
3. **반환·상태:** 관리 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source 필수, --row는 int이며 기본값 1이다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하며 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** 빈 입력과 범위를 벗어난 1-based --row를 거절한다. 선택되지 않은 행도 make_context_document로 검증한다. OSError·ValueError·TypeError·KeyError·PyMongoError를 CommandError로 바꾼다.
2. **직접 호출:** read_ndjson → 모든 행의 make_context_document → 선택 행의 apply_context → get_db → player_context.find_one → get_context → json.dumps → stdout.write.
3. **반환·상태:** database·source·row·input_rows·status·key·incoming_version·stored_version·stored_document·context를 JSON 표준 출력한다. 전체 파일을 반영하지 않으며 쓰기 후 조회/출력에 실패해도 반영은 남을 수 있다.
