# `ads/management/commands/demo_context_versions.py`

원본 소스 경로: `ads/management/commands/demo_context_versions.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

새 teaching-fixture subject에 실제 Mongo 쓰기를 수행해 버전·반복·충돌·삭제 표시를 관찰한다. 실행 후 최종 tombstone 문서가 남는다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django가 옵션 등록과 handle을 호출한다.
3. **반환·상태:** 관리 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --subject 필수다. media_id는 settings.ADS_MEDIA_ID를 사용한다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하며 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** fixture- 뒤에 내용이 있는 새 subject를 요구하며 기존 _id는 거절한다. 기대한 version_conflict만 관찰 상태로 기록한다. OSError·ValueError·TypeError·KeyError·PyMongoError를 CommandError로 변환한다.
2. **직접 호출:** context_subject_key → get_db → find_one → 내부 change/observe → apply_context → find_one → get_context → JSON 표준 출력.
3. **반환·상태:** first=applied, newer=applied, repeat=duplicate, older=stale, conflict=version_conflict, delete=applied, older-after-delete=stale 순서로 관찰한다. database·key·steps·stored_document·visible_context를 출력한다. 삭제 후 version=3·deleted=True·context={}가 남고 visible_context={}다. 중간 실패 시 이전 저장을 되돌리지 않는다.

### handle 내부 함수

`change(version, coins, op="upsert")`는 고정 UTC 시각 `2026-10-13T00:00:00+00:00`과 fixture-room으로 9필드 변경을 만들고 change_id를 계산한다. `observe(label, row, expect_conflict=False)`는 반영 전후 Mongo 문서를 읽고 incoming_version·stored_version·stored_coins·deleted·unchanged를 기록한다. 기대한 충돌이 발생하지 않으면 오류다. 이 두 함수는 모듈의 외부 진입점이 아니다.
