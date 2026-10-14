# `ads/management/commands/export_context_handoff.py`

원본 소스 경로: `ads/management/commands/export_context_handoff.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

완료된 정규화 입력·위치·현재 Mongo 공개 문서를 새 인계 폴더로 묶는다. [호출 계약](../../context_projection.py.md).

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django 관리 명령 로더 → add_arguments·handle.
3. **반환·상태:** 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source·--checkpoint·--output-dir 필수, --media-id 기본값 settings.ADS_MEDIA_ID다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하고 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** 등록된 옵션을 받아 아래 계약을 적용한다.
2. **직접 호출:** export_context_handoff → json.dumps(ensure_ascii=False) → stdout.write.
3. **반환·상태:** manifest JSON을 표준 출력한다. OSError·ValueError·TypeError·KeyError·PyMongoError를 CommandError로 변환한다. Mongo 조회와 파일 쓰기를 수행한다.
