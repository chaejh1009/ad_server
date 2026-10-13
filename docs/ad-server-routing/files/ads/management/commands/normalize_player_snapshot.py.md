# `ads/management/commands/normalize_player_snapshot.py`

원본 소스 경로: `ads/management/commands/normalize_player_snapshot.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

수신 계약과 원본을 대조한 뒤 전체 공개 행을 정규화 NDJSON으로 저장한다. [context_projection](../../context_projection.py.md)의 파일 처리 경로이며 Mongo에는 반영하지 않는다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django가 옵션 등록과 handle을 호출한다.
3. **반환·상태:** 관리 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source·--contract·--output은 필수다. --media-id 기본값은 settings.ADS_MEDIA_ID다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하며 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** OSError·TypeError·ValueError·KeyError를 CommandError로 변환한다. 전체 행 검증과 원본/계약 경로 보호·임시 파일 교체는 normalize_snapshot_file이 담당한다.
2. **직접 호출:** normalize_snapshot_file → json.dumps(ensure_ascii=False, sort_keys=True, indent=2) → self.stdout.write.
3. **반환·상태:** 출력 경로·행 수·출력/원본 SHA-256·스키마·출처·매체·op_counts·unique_change_ids·첫 행 preview를 JSON 표준 출력한다.
