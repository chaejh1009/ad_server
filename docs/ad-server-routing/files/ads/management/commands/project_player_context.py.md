# `ads/management/commands/project_player_context.py`

원본 소스 경로: `ads/management/commands/project_player_context.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

정규화 파일을 순서대로 Mongo에 반영하고 체크포인트로 재개한다. [context_projection](../../context_projection.py.md)의 project_context_file을 사용한다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django가 옵션 등록과 handle을 호출한다.
3. **반환·상태:** 관리 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source 필수, --checkpoint 선택, --limit은 선택 int다. 현재 구현에서는 비어 있지 않은 입력에 checkpoint를 반드시 지정해야 정상 전진한다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하며 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** OSError·ValueError·TypeError·KeyError·PyMongoError를 CommandError로 변환한다. 계약/행/위치 검증과 저장은 서비스에 위임한다.
2. **직접 호출:** project_context_file(source, checkpoint, limit) → json.dumps → stdout.write.
3. **반환·상태:** processed·applied·skipped·counts·start_line·next_line·rows·done·source_sha256·checkpoint_path·checkpoint_state를 JSON 표준 출력한다. Mongo와 위치 파일은 별도 저장 단계다.
