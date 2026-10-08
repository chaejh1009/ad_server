# `ads/management/commands/build_ad_reports.py`

원본 소스 경로: `ads/management/commands/build_ad_reports.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

고정 광고 NDJSON에서 [reporting.build_daily_reports](../../reporting.py.md)로 일별 보고서 후보 파일을 만드는 Django 관리 명령이다. Mongo 게시와 분리된다.

## `class Command`

Signature: `class Command(BaseCommand)`

BaseCommand를 상속한다. help는 고정 광고 NDJSON에서 일별 보고서 후보 계산을 설명한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source·--output 두 옵션을 필수로 등록한다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하며 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** options에서 source·output 경로를 읽는다. 직접 스키마 검증을 하지 않는다.
2. **직접 호출:** read_ndjson(source) → build_daily_reports(rows) → write_ndjson(output, rows) → json.dumps → self.stdout.write.
3. **반환·상태:** rows·sha256·path JSON을 표준 출력하고 후보 NDJSON을 쓴다. publish_reports를 호출하지 않아 Mongo에 게시하지 않는다.
