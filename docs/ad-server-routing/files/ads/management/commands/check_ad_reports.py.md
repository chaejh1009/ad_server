# `ads/management/commands/check_ad_reports.py`

원본 소스 경로: `ads/management/commands/check_ad_reports.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

전체 보관 사건의 고정 NDJSON으로 기대 보고서를 다시 계산하고 Mongo 게시 결과와 대조하여 JSON 증거를 저장한다. [reporting](../../reporting.py.md)·[exporting](../../exporting.py.md)에 의존한다.

## `class Command`

Signature: `class Command(BaseCommand)`

Django BaseCommand를 상속하며 명령의 help·옵션·실행 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source·--output을 필수로 등록한다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하며 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** options의 파일 경로를 사용한다. 입력 내용 검증은 호출 서비스가 수행한다.
2. **직접 호출:** Path → read_ndjson → build_daily_reports → get_db().ad_daily_reports.find() → hashlib.sha256(source.read_bytes()) → 출력 부모 mkdir → JSON write_text → self.stdout.write.
3. **반환·상태:** 기대에만 있는 키·게시본에만 있는 키·값이 다른 공통 키를 각각 정렬한다. 비교 필드는 impressions·clicks·ctr·bid_units_sum·source_max_event_time이며 generated_at은 비교하지 않는다. 세 목록이 모두 비면 ok=True다. 출력 JSON을 저장·출력한 뒤 불일치 시 CommandError로 실패 종료한다. 그 이전 파일·집계·Mongo 오류는 전파한다. 게시 데이터를 변경하지 않는다.

증거에는 artifact_id="village-lab.ads-analytics"·artifact_version="v2"·source_kind="ad-events"·source_sha256·source_rows·unique_events·missing_report_keys·extra_report_keys·different_report_keys·ok·observed_at(현재 UTC ISO)와 transport="file"·spark_ad_job_status="not-configured"·gui_status="separate-manual-observation"이 들어간다. 전체 게시 컬렉션과 비교하므로 부분 날짜 입력은 다른 날짜 행을 extra로 판정할 수 있다.
