# `ads/management/inspect_player_context.py`

원본 소스 경로: `ads/management/inspect_player_context.py` · [전체 라우팅](../../../README.md)

## 책임과 경계

commands/ 밖에 있는 보조 Command 모듈이다. Django 관리 명령 자동 탐색 대상이 아니며 실제 inspect_player_context CLI는 [commands/inspect_player_context.py](commands/inspect_player_context.py.md)가 담당한다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django가 옵션 등록과 handle을 호출한다.
3. **반환·상태:** 관리 명령 진입점을 정의한다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** 별도 입력 검증이나 예외 변환이 없다. Mongo 오류를 호출자에게 전파한다.
2. **직접 호출:** get_db → player_context.create_index → find({}, projection) → list → json.dumps → stdout.write.
3. **반환·상태:** 동일한 media_subject_once 고유 인덱스를 생성하고 모든 매체의 _id·media_id·subject_id·version·deleted·source_kind만 조회한다. count·rows를 JSON 표준 출력한다. 정렬은 지정하지 않는다.
