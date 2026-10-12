import hashlib
import json
import os
import tempfile
from pathlib import Path

from .exporting import write_ndjson
from .snapshot_intake import (
    PUBLIC_FIELDS,
    SNAPSHOT_FIELDS,
    SCHEMA_VERSION,
    SOURCE_KIND,
    _check_public_state,
    _read_snapshot,
    inspect_snapshot,
)
from .timestamps import parse_utc


def read_snapshot_package(source, contract_path):
    """24일차의 동결된 원문·수신 계약을 소비하기 직전에 대조한다."""
    source = Path(source)
    contract_path = Path(contract_path)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if not isinstance(contract, dict):
        raise ValueError("계약은 JSON 객체여야 합니다.")
    inspected = inspect_snapshot(source)
    expected = {
        **inspected,
        "artifact_id": "data/exports/player-cdc.ndjson",
        "artifact_version": "v2",
        "collector": "game.export_player_snapshot",
        "binlog_cdc_status": "not-configured",
        "position_kind": "file-line",
        "kafka_position": None,
        "public_fields": list(PUBLIC_FIELDS),
    }
    for field, value in expected.items():
        if (field not in contract
                or json.dumps(contract[field], sort_keys=True)
                != json.dumps(value, sort_keys=True)):
            raise ValueError(f"계약과 원본이 다릅니다: {field}")
    parse_utc(contract.get("created_at"))
    declared_path = contract.get("source_path")
    if not isinstance(declared_path, str) or not declared_path:
        raise ValueError("계약 source_path가 없습니다.")
    if Path(declared_path).resolve() != source.resolve():
        raise ValueError("계약 source_path와 --source가 다릅니다.")
    # 같은 bytes에서 얻은 행·SHA를 사용한다. 검사 후 변경도 거절한다.
    rows, checksum = _read_snapshot(source)
    if checksum != inspected["sha256"]:
        raise ValueError("검사 후 원본이 변경됐습니다.")
    return rows, inspected

def normalize_snapshot(row, media_id="village-game"):
    if not isinstance(row, dict) or set(row) != SNAPSHOT_FIELDS:
        raise ValueError("공개 snapshot의 정확한 8개 필드가 필요합니다.")
    if row["schema_version"] != SCHEMA_VERSION or row["source_kind"] != SOURCE_KIND:
        raise ValueError("player-snapshot/v1 공개 입력이 필요합니다.")
    if not isinstance(media_id, str) or not media_id.strip():
        raise ValueError("media_id는 비어 있지 않은 문자열이어야 합니다.")
    # [문제 1 · 한 줄] 공개 다섯 필드만 골라 기존 공개 상태 검사 helper에 전달한다.
    # 예시: check_score({name: item[name] for name in SCORE_FIELDS})
    _check_public_state({field: row[field] for field in PUBLIC_FIELDS})

    parse_utc(row["captured_at"])
    # [문제 2 · 여러 줄] 대상 문자열·UTC 수정 시각·공개 context를 만든다. (4줄)
    # 예시: item_id = str(item["id"])
    #       instant = parse_utc(item["when"]).isoformat()
    #       detail = {"item_id": item_id, "title": item["title"],
    #                 "when": instant}
    subject_id = str(row["id"])
    updated_at = parse_utc(row["updated_at"]).isoformat()
    context = {"player_id": subject_id, "room_id": row["room_id"], "coins":row["coins"],
                "version": row["version"], "updated_at": updated_at}

    # [문제 3 · 여러 줄] 위 출력 계약의 정규화 사전을 change로 만든다. (4줄)
    # 예시: packet = {"schema_version": "score-change/v1",
    #                "source_kind": "score-file", "group_id": group_id,
    #                "item_id": item_id, "op": "replace",
    #                "when": instant, "detail": detail}
    change = {"schema_version": "player-context-change/v1",
                "source_kind": SOURCE_KIND, "media_id": media_id,
                "subject_id": subject_id, "op": "upsert", "version": row["version"],
                "event_time": updated_at, "context": context}

    # [문제 4 · 한 줄] UTF-8 해시에 사용할 정렬 JSON 문자열을 canonical에 담는다.
    # 예시: text = json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    canonical = json.dumps(change, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    # [문제 5 · 한 단어] SHA-256 결과를 해시 문자열로 반환하는 메서드 이름이다.
    # 힌트 5: 파일 checksum에서도 사용한 문자열 반환 메서드다.
    change["change_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return change