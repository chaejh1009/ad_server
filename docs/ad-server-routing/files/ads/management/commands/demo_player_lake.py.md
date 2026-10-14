# `ads/management/commands/demo_player_lake.py`

원본 소스 경로: `ads/management/commands/demo_player_lake.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

별도 메모리 fixture로 중복·버전·삭제·거절을 관찰한다. [Lake 함수](../../lake_files.py.md)를 호출한다.

## `def fixture_change(version, coins=10, op='upsert')`

Signature: `def fixture_change(version, coins=10, op='upsert')`

1. **검증·변환:** 입력 인수를 별도 검증하지 않고 version으로 고정 2026-10-14 UTC 시각을 구성한다. delete는 빈 context, 그 외는 공개 5필드다.
2. **직접 호출:** stable_json → hashlib.sha256.
3. **반환·상태:** village-game/fixture-lake의 teaching-fixture 변경 사전을 반환한다. change_id는 자신을 넣기 전 정렬 JSON의 SHA다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django 관리 명령 로더 → add_arguments·handle.
3. **반환·상태:** 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --case 필수: duplicates·invalid-schema·change-id-conflict·versions·delete·version-conflict·empty 중 하나다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하고 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** 등록된 옵션을 받아 아래 계약을 적용한다.
2. **직접 호출:** fixture_change → case별 행 구성 → build_history → duplicates 외 build_current → json.dumps → stdout.write.
3. **반환·상태:** case·source_kind=teaching-fixture·입력/history/current 행 수·current·written=False·database_changed=False를 출력한다. duplicates는 current 계산을 생략한다. invalid-schema·change-id-conflict·version-conflict는 CommandError로 실패한다. ValueError·TypeError·KeyError를 변환하며 파일·DB를 수정하지 않는다.
