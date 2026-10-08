# `ads/management/commands/deliver_ad_events.py`

원본 소스 경로: `ads/management/commands/deliver_ad_events.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

로컬 파일로 미전달 광고 사건을 전달한다. [delivery](../../delivery.py.md)의 한 writer·재시도 계약을 따른다.

## `class Command`

Signature: `class Command(BaseCommand)`

Django BaseCommand를 상속하며 명령의 help·옵션·실행 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --output 필수, --limit은 int이며 기본 100이다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하며 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** options의 파일 경로를 사용한다. 입력 내용 검증은 호출 서비스가 수행한다.
2. **직접 호출:** deliver_events(options["output"], options["limit"]) → json.dumps(ensure_ascii=False) → self.stdout.write.
3. **반환·상태:** processed·total·pending JSON을 표준 출력한다. NDJSON 교체와 Mongo 표식 변경은 delivery에서 수행한다. 오류는 전파한다.
