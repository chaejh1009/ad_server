# `ads/management/commands/inspect_player_snapshot.py`

원본 소스 경로: `ads/management/commands/inspect_player_snapshot.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

저장된 플레이어 공개 스냅샷을 [snapshot_intake.inspect_snapshot](../../snapshot_intake.py.md)으로 검사하고 JSON 요약을 표준 출력하는 Django 관리 명령이다. 파일·DB를 수정하지 않는다.

## `class Command`

Signature: `class Command(BaseCommand)`

Django BaseCommand를 상속하며 help·옵션·실행 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source를 필수 옵션으로 등록한다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하며 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** options["source"]를 검사 서비스에 전달한다. OSError·ValueError·TypeError·KeyError를 잡아 예외 원인을 유지한 CommandError로 바꾼다.
2. **직접 호출:** inspect_snapshot → json.dumps(ensure_ascii=False, sort_keys=True) → self.stdout.write.
3. **반환·상태:** 정상 시 rows·public_ids·source_kind·schema_version·captured_at·sha256 JSON을 표준 출력한다. 검사 실패는 CommandError로 실패 종료한다. 별도 결과 파일은 만들지 않는다.
