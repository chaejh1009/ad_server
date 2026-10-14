# `ads/management/commands/export_day26_ad_events.py`

원본 소스 경로: `ads/management/commands/export_day26_ad_events.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

기존 사건 내보내기를 임시 파일로 실행하고 검증한 뒤 새 고정 사건 파일로 옮긴다. [사건 내보내기](../../exporting.py.md).

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django 관리 명령 로더 → add_arguments·handle.
3. **반환·상태:** 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --output 필수, --since·--until 선택이다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하고 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** 등록된 옵션을 받아 다음 계약을 적용한다.
2. **직접 호출:** Path.exists → 부모 mkdir → TemporaryDirectory → export_ad_events → read_ndjson → 필드/schema·ID 중복 검사 → read_bytes·SHA 대조 → staged.rename(path) → stdout.write.
3. **반환·상태:** 기존 출력 경로를 거절하고 ad-event/v1의 정확한 공개 12필드·고유 event_id·반환 SHA와 파일 SHA 일치를 검사한다. path·rows·unique_events·sha256·schema_version·source_kind=ad-events·since/until·첫 행 preview를 출력한다. 빈 입력도 허용하며 manifest는 만들지 않는다. OSError·ValueError·KeyError·TypeError·PyMongoError는 CommandError다. 임시 파일은 실패 시 정리하지만 부모는 남을 수 있다. exists 검사와 rename 사이의 동시 작성자 경합은 조정하지 않는다. Mongo는 조회만 한다.
