# `ads/management/commands/load_ad_reports.py`

원본 소스 경로: `ads/management/commands/load_ad_reports.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

후보 NDJSON의 업무 키별 보고서를 Mongo에 게시한다. [reporting](../../reporting.py.md)의 행 검증·replace upsert 계약을 따른다.

## `class Command`

Signature: `class Command(BaseCommand)`

Django BaseCommand를 상속하며 명령의 help·옵션·실행 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source를 필수로 등록한다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하며 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** options의 파일 경로를 사용한다. 입력 내용 검증은 호출 서비스가 수행한다.
2. **직접 호출:** read_ndjson(options["source"]) → publish_reports → self.stdout.write.
3. **반환·상태:** published=처리행수를 출력한다. 입력에 없는 기존 보고서 행은 삭제하지 않는다. 행별 게시이므로 뒤 행의 실패가 앞 행을 되돌리지 않는다. 오류는 전파한다.
