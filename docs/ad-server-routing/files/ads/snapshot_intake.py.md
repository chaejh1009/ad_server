# `ads/snapshot_intake.py`

원본 소스 경로: `ads/snapshot_intake.py` · [전체 라우팅](../../README.md)

## 책임과 경계

동결된 플레이어 공개 스냅샷 NDJSON의 필드·타입·출처·수집 시각을 검사한다. [inspect_player_snapshot 명령](management/commands/inspect_player_snapshot.py.md)이 호출한다. 파일을 한 번 읽은 바이트로 검증과 SHA-256 계산을 수행한다. HTTP 경로·Mongo 저장·게임 ORM 접근은 없다. 단일 작성자와 사용 완료까지 입력 불변을 전제로 하며 파일 잠금은 제공하지 않는다.

## `def _read_snapshot(path)`

Signature: `def _read_snapshot(path)`

1. **검증·변환:** Path(path).read_bytes로 전체 파일을 한 번 읽고 UTF-8로 해석한다. 각 줄을 json.loads로 읽으며 빈 줄·dict가 아닌 값은 행 번호가 포함된 ValueError다. 빈 파일은 빈 목록이다.
2. **직접 호출:** Path.read_bytes → io.StringIO → enumerate → json.loads → hashlib.sha256(payload).hexdigest.
3. **반환·상태:** (행 목록, 원본 바이트 SHA-256 문자열)을 반환한다. 파일·UTF-8·JSON 오류를 전파하고 저장 상태를 변경하지 않는다.

## `def _check_public_state(row)`

Signature: `def _check_public_state(row)`

1. **검증·변환:** dict의 키가 id·room_id·coins·version·updated_at 다섯 개와 정확히 일치해야 한다. id는 양수 int, room_id는 문자열, coins는 int, version은 0 이상 int여야 한다. 정수 검사에서 bool을 거절한다. 빈 room_id와 음수 coins는 별도로 거절하지 않는다.
2. **직접 호출:** [parse_utc](timestamps.py.md)(row["updated_at"])로 시간대 있는 시각인지 검사한다.
3. **반환·상태:** 정상 반환값은 None이다. 입력을 수정하지 않으며 검증 오류는 ValueError 등으로 전파한다. 파싱한 UTC 시각으로 원본 문자열을 교체하지 않는다.

## `def inspect_snapshot(path)`

Signature: `def inspect_snapshot(path)`

1. **검증·변환:** 모든 행에 공개 다섯 필드와 schema_version·source_kind·captured_at, 정확히 여덟 키를 요구한다. schema_version="player-snapshot/v1", source_kind="player-snapshot"이어야 한다. 공개 상태를 검사하고 같은 id의 재등장은 내용이 같아도 거절한다. captured_at은 시간대 있는 시각이어야 하며 모든 행의 원본 값이 같아야 한다. 같은 순간이라도 다른 문자열 표현이면 다른 수집으로 거절한다.
2. **직접 호출:** _read_snapshot → 각 행의 _check_public_state → parse_utc(captured_at) → sorted(seen).
3. **반환·상태:** rows·public_ids(정렬된 ID 목록)·source_kind·schema_version·captured_at·sha256 사전을 반환한다. 빈 파일도 허용하며 rows=0·public_ids=[]·captured_at=None이다. 오류를 전파하며 파일이나 DB를 수정하지 않는다.

## 현재 사용 범위

광고 사건 파일과 별개인 플레이어 공개 상태 검사다. 검사 결과를 광고 선택 context나 보고서에 자동 반영하지 않는다. 계정·좌표 등 추가 필드는 정확한 필드 집합 검사로 거절한다. exporting의 NDJSON 유틸리티 등이 import되어 있지만 현재 실행 경로는 위의 전용 읽기 함수만 사용한다.
