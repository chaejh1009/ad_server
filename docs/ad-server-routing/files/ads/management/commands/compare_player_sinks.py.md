# `ads/management/commands/compare_player_sinks.py`

원본 소스 경로: `ads/management/commands/compare_player_sinks.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

동일 원본을 재계산해 Lake 결과를 검증한 뒤 Mongo 공개 상태와 대조하고 JSON 증거를 저장한다. [대조 함수](../../sink_evidence.py.md).

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django 관리 명령 로더 → add_arguments·handle.
3. **반환·상태:** 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source·--lake-dir·--output 필수, --media-id 기본값 settings.ADS_MEDIA_ID다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하고 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** 등록된 옵션을 받아 다음 계약을 적용한다.
2. **직접 호출:** resolve/samefile 출력 보호 → read_lake_manifest → _read_context_changes → build_history/build_current → read_ndjson(두 결과)·재계산 결과 비교 → compare_context_to_current → output.write_text → stdout.write.
3. **반환·상태:** 출력은 원본·manifest·history·current와 같은 resolve 경로나 존재하는 hard link면 거절한다. 원본 SHA/행 수와 두 Lake 결과 전체 값이 같아야 Mongo 대조를 시작한다. 결과에는 원본 경로/SHA·Lake 경로·매체·current SHA·same_source_verified=True·대조 필드가 있다. JSON 파일 저장 후 path를 추가해 표준 출력하므로 파일에는 path가 없다. 누락/불일치가 있어도 정상 종료하며 추가 Mongo 대상은 별도 기록한다. OSError·ValueError·KeyError·TypeError·PyMongoError를 CommandError로 변환한다. DB는 조회만 하고 출력은 직접 덮어쓴다.
