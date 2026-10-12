# `ads/management/commands/read_snapshot_missing.py`

원본 소스 경로: `ads/management/commands/read_snapshot_missing.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

동결된 두 공개 스냅샷을 [snapshot_intake.load_rows](../../snapshot_intake.py.md#def-load_rowspath)로 읽고 [missing_summary](../../snapshot_intake.py.md#def-missing_summarybefore-after)로 이전에만 남은 ID를 기록하는 Django 관리 명령이다. 누락을 삭제 사건으로 추론하지 않으며 DB·Mongo·게임 ORM·CDC를 변경하지 않는다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속하며 옵션 등록과 실행 진입점을 정의한다.
2. **직접 호출:** 클래스 선언 자체의 직접 호출은 없고 Django가 add_arguments와 handle을 호출한다.
3. **반환·상태:** help는 스냅샷 누락을 삭제 사건으로 바꾸지 않고 기록함을 설명한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --before·--after·--output을 모두 필수 옵션으로 등록한다. 별도 type 변환은 없다.
2. **직접 호출:** parser.add_argument를 세 번 호출한다.
3. **반환·상태:** parser를 변경하며 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** before·after를 각각 load_rows로 검사·재읽기한 뒤 missing_summary에 전달한다. output의 resolve 결과가 두 입력 중 하나와 같으면 ValueError다. before와 after가 같은 경로인 것은 허용한다. resolve 비교는 서로 다른 경로의 hard link까지 구분하지 않는다. 부모 디렉터리는 parents=True·exist_ok=True로 생성한다. OSError·ValueError·TypeError·KeyError는 원인 예외를 유지한 CommandError로 바꾼다.
2. **직접 호출:** 두 번의 [load_rows](../../snapshot_intake.py.md#def-load_rowspath) → [missing_summary](../../snapshot_intake.py.md#def-missing_summarybefore-after) → Path.resolve → target.parent.mkdir → json.dumps(ensure_ascii=False, sort_keys=True, indent=2) → target.write_text(encoding="utf-8") → json.dumps(ensure_ascii=False, sort_keys=True) → self.stdout.write.
3. **반환·상태:** UTF-8·2칸 들여쓰기·마지막 개행 JSON을 output에 덮어쓰고 같은 결과를 정렬된 키의 한 줄 JSON으로 표준 출력한다. 누락 ID가 있어도 정상 종료한다. 파일 교체는 원자적이지 않으며 stdout은 try 바깥이다. 명시적 반환값은 없다.

### JSON 출력 계약

| 필드 | 값·조건 |
| --- | --- |
| unknown | before에만 있고 after에는 없는 ID를 정렬한 목록 |
| source_kind | `"snapshot-comparison"` |
| delete_events | 항상 `[]` |
| delete_inference_allowed | 항상 `False` |

값 변경이나 새 ID는 이 명령의 출력 대상이 아니다. 해당 비교는 [compare_player_snapshots](compare_player_snapshots.py.md)가 맡는다. 두 입력은 load_rows의 검사와 재읽기 사이에도 동결되어 있어야 하며 잠금이나 두 읽기의 체크섬 대조는 없다. 명시적 d 교육 이벤트는 [write_player_change_fixture](write_player_change_fixture.py.md)의 별도 경로다.
