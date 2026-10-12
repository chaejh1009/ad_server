# `ads/management/commands/compare_player_snapshots.py`

원본 소스 경로: `ads/management/commands/compare_player_snapshots.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

동결된 두 공개 스냅샷을 ID별로 비교하고 JSON 결과를 파일과 표준 출력으로 기록한다. Mongo·게임 ORM·CDC 연결은 없다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속하며 옵션 등록과 실행 진입점을 정의한다.
2. **직접 호출:** 클래스 선언 자체의 직접 호출은 없고 Django가 add_arguments와 handle을 호출한다.
3. **반환·상태:** help는 동결된 두 파일의 공개 상태를 ID 기준으로 비교함을 설명한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --before·--after·--output을 모두 필수 옵션으로 등록한다. 별도 type 변환은 없다.
2. **직접 호출:** parser.add_argument를 세 번 호출한다.
3. **반환·상태:** parser를 변경하며 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** before와 after를 각각 load_rows로 검사·재읽기한 뒤 compare에 전달한다. 출력 경로의 resolve 결과가 두 입력 중 하나와 같으면 ValueError다. 두 입력끼리 같은 경로인 것은 허용한다. resolve 비교는 서로 다른 경로의 hard link까지 식별하지 않는다.
2. **직접 호출:** [load_rows·compare](../../snapshot_intake.py.md) → Path.resolve → target.parent.mkdir(parents=True, exist_ok=True) → json.dumps(ensure_ascii=False, sort_keys=True, indent=2) → target.write_text(encoding="utf-8") → self.stdout.write.
3. **반환·상태:** changed·newly_seen·missing_unknown JSON을 2칸 들여쓰기와 마지막 개행으로 파일에 덮어쓰고 같은 결과를 들여쓰기 JSON으로 표준 출력한다. 차이가 있어도 정상 종료한다. 누락 ID는 삭제 증거가 아니다. OSError·ValueError·TypeError·KeyError는 원인을 유지한 CommandError로 바꾸며 stdout 쓰기는 try 바깥이다. 파일 교체는 원자적이지 않다. 명시적 반환값은 없다.

### JSON 출력 계약

| 필드 | 값·조건 |
| --- | --- |
| changed | 공통 ID의 room_id·coins·version·UTC updated_at 중 하나라도 다르면 id·before_version·after_version·before_coins·after_coins를 담는 목록. ID 순으로 정렬한다. room_id·updated_at의 전후 값은 출력하지 않는다. |
| newly_seen | after에만 있는 ID를 정렬한 목록 |
| missing_unknown | before에만 있는 ID를 정렬한 목록. 삭제 사건으로 해석하지 않는다. |

captured_at 등 수집 메타데이터는 상태 비교에서 제외하고, updated_at의 문자열 표현이 달라도 같은 UTC 순간이면 동일하다. 두 입력은 load_rows의 검사와 재읽기 사이에도 동결되어 있어야 하며 잠금이나 두 읽기의 체크섬 대조는 없다.
