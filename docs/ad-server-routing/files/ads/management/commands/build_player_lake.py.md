# `ads/management/commands/build_player_lake.py`

원본 소스 경로: `ads/management/commands/build_player_lake.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

고정 정규화 파일에서 새 Player Lake 버전을 저장한다. [Lake 생성 계약](../../lake_files.py.md).

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django 관리 명령 로더 → add_arguments·handle.
3. **반환·상태:** 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source·--output 필수다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하고 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** 등록된 옵션을 받아 다음 계약을 적용한다.
2. **직접 호출:** build_lake_version → json.dumps(ensure_ascii=False) → stdout.write.
3. **반환·상태:** manifest JSON을 표준 출력한다. OSError·ValueError·KeyError·TypeError는 CommandError로 변환한다. 새 출력 디렉터리의 파일을 생성하며 DB를 수정하지 않는다.
