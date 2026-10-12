# `ads/management/commands/write_player_change_fixture.py`

원본 소스 경로: `ads/management/commands/write_player_change_fixture.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

실제 CDC와 구별되는 teaching-fixture 출처의 고정 r/u/d 이벤트 세 행과 해석 요약을 저장한다. 원본 스냅샷 입력·DB 변경·CDC 접속은 없다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속하며 옵션 등록과 실행 진입점을 정의한다.
2. **직접 호출:** 클래스 선언 자체의 직접 호출은 없고 Django가 add_arguments와 handle을 호출한다.
3. **반환·상태:** help는 실제 CDC와 구별한 r/u/d 교육 fixture와 해석 결과를 저장함을 설명한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --output은 필수, --summary는 선택 옵션으로 등록한다. summary를 생략하면 None이며 별도 type 변환은 없다.
2. **직접 호출:** parser.add_argument를 두 번 호출한다.
3. **반환·상태:** parser를 변경하며 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** id=1·room_id="room-01"의 coins=0/version=0 상태와 coins=30/version=1 상태를 만든다. updated_at은 각각 "2026-10-08T00:00:00+00:00"과 "2026-10-08T00:01:00+00:00"이다. r은 None→원본, u는 원본→수정, d는 수정→None이다. summary가 참인 값이고 output과 resolve 결과가 같으면 ValueError다. resolve 비교는 서로 다른 경로의 hard link까지 식별하지 않는다.
2. **직접 호출:** Path.resolve → 각 이벤트의 [change_player](../../snapshot_intake.py.md) → [exporting.write_ndjson](../../exporting.py.md) → 선택 summary의 parent.mkdir·write_text → json.dumps → self.stdout.write.
3. **반환·상태:** output을 세 행의 NDJSON으로 덮어쓴다. 요약은 path·source_kind="teaching-fixture"·rows=3·sha256·interpreted다. interpreted의 r/u/d는 player_id=1, coins=0/30/30, version=0/1/1, deleted=False/False/True다. summary를 지정하면 UTF-8·2칸 들여쓰기·마지막 개행 JSON으로 덮어쓰고, 항상 정렬된 키의 한 줄 JSON을 표준 출력한다. OSError·ValueError·TypeError·KeyError는 원인을 유지한 CommandError로 바꾸며 stdout 쓰기는 try 바깥이다. 두 출력은 별도 저장이므로 summary 실패 후 fixture 파일이 남을 수 있다. 명시적 반환값은 없다.

빈 문자열 summary는 생략한 것처럼 처리한다. NDJSON의 각 행에는 source_kind·op·before·after가 있으며 삭제 d의 before는 수정 상태다. 해석 결과의 deleted=True는 고정 교육 fixture의 명시적 d에서 나온 값이며, 스냅샷 비교의 누락 ID를 삭제로 추론한 값이 아니다. output의 저장·체크섬 계산은 가져온 [write_ndjson](../../exporting.py.md)에 위임한다.
