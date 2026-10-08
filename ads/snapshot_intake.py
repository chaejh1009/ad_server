"""동결된 플레이어 스냅샷을 검사하는 24일차 파일 실습.

입력 파일은 검사부터 사용 완료까지 변경하지 않는다. 단일 작성자를 전제로
하며 실행 중 다른 프로세스의 파일 변경을 막는 잠금은 제공하지 않는다.
"""
import hashlib
import io
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .exporting import read_ndjson, write_ndjson
from .timestamps import parse_utc


SCHEMA_VERSION = "player-snapshot/v1"
SOURCE_KIND = "player-snapshot"
PUBLIC_FIELDS = ("id", "room_id", "coins", "version", "updated_at")
SNAPSHOT_FIELDS = set(PUBLIC_FIELDS) | {"schema_version", "source_kind", "captured_at"}


def _read_snapshot(path):
    """검증할 행과 체크섬을 같은 한 번의 bytes 읽기에서 얻는다."""
    payload = Path(path).read_bytes()
    rows = []
    for number, line in enumerate(io.StringIO(payload.decode("utf-8")), 1):
        if not line.strip():
            raise ValueError(f"빈 행 {number}")
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"문서가 아닌 행 {number}")
        rows.append(row)
    return rows, hashlib.sha256(payload).hexdigest()


def _check_public_state(row):
    """게임 계정·좌표를 받지 않는 공개 상태의 형식 검사."""
    if not isinstance(row, dict) or set(row) != set(PUBLIC_FIELDS):
        raise ValueError("공개 상태는 id, room_id, coins, version, updated_at만 받습니다.")
    if type(row["id"]) is not int or row["id"] <= 0:
        raise ValueError("id는 양의 정수여야 합니다.")
    if not isinstance(row["room_id"], str):
        raise ValueError("room_id는 문자열이어야 합니다.")
    if type(row["coins"]) is not int:
        raise ValueError("coins는 정수여야 합니다.")
    if type(row["version"]) is not int or row["version"] < 0:
        raise ValueError("version은 0 이상의 정수여야 합니다.")
    parse_utc(row["updated_at"])

def inspect_snapshot(path):
    rows, checksum = _read_snapshot(path)
    seen = set()
    captured_at = None
    for row in rows:
        # [문제 1 · 여러 줄] 정확한 8필드와 snapshot 스키마·출처를 검사한다. (4줄)
        # 예시: if set(entry) != ALLOWED:
        #           raise ValueError("필드 오류")
        #       if entry["schema"] != EXPECTED_SCHEMA or entry["kind"] != EXPECTED_KIND:
        #           raise ValueError("출처 오류")
        if set(row) != SNAPSHOT_FIELDS:
            raise ValueError("필드 오류")
        if row["schema_version"] != SCHEMA_VERSION or row["source_kind"] != SOURCE_KIND:
            raise ValueError("출처 오류")

        # [문제 2 · 한 줄] 공개 다섯 필드 사전을 만들어 제공 검사에 전달한다.
        # 예시: check_score({name: entry[name] for name in SCORE_FIELDS})
        _check_public_state({field: row[field] for field in PUBLIC_FIELDS})

        # [문제 3 · 여러 줄] 이미 본 ID는 거절하고 새 ID만 등록한다. (3줄)
        # 예시: if entry["code"] in known:
        #           raise ValueError("중복 코드")
        #       known.add(entry["code"])
        if row["id"] in seen:
            raise ValueError("중복 코드")
        seen.add(row["id"])

        # [문제 4 · 한 단어] 수집 시각의 시간대까지 확인할 기존 helper 이름이다.
        # 힌트 4: ads.timestamps에서 import했고 23일차 export에도 사용했다.
        parse_utc(row["captured_at"])

        # [문제 5 · 여러 줄] 첫 수집 시각을 보관하고 후속 행의 다른 값은 거절한다. (4줄)
        # 예시: if batch_key is None:
        #           batch_key = entry["batch"]
        #       elif entry["batch"] != batch_key:
        #           raise ValueError("같은 수집이 아님")
        if captured_at is None:
            captured_at = row["captured_at"]
        elif row["captured_at"] != captured_at:
            raise ValueError("같은 수집이 아님")

    return {"rows": len(rows), "public_ids": sorted(seen),
            "source_kind": SOURCE_KIND, "schema_version": SCHEMA_VERSION,
            "captured_at": captured_at, "sha256": checksum}