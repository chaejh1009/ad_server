# `ads/management/commands/export_ad_events.py`

원본 소스 경로: `ads/management/commands/export_ad_events.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

Django의 export_ad_events 관리 명령이다. HTTP 인증 대신 서버 CLI에서 실행한다. 실제 파일·Mongo 처리는 [exporting](../../exporting.py.md)에 위임한다.

## `class Command`

Signature: `class Command(BaseCommand)`

BaseCommand를 상속하며 Django가 명령 이름으로 로드한다. help는 공개 사건의 [since, until) NDJSON 내보내기를 설명한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --output은 필수, --since·--until은 선택 문자열 옵션이다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser에 옵션을 등록하며 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** options에서 output·since·until을 읽는다. 시간 검증은 서비스에 위임한다.
2. **직접 호출:** export_ad_events(output, since, until) → json.dumps(ensure_ascii=False) → self.stdout.write.
3. **반환·상태:** 서비스의 메타데이터 JSON을 표준 출력한다. 오류를 CommandError로 감싸지 않고 전파한다. 출력 파일은 서비스가 덮어쓴다.
