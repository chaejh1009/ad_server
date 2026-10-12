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

def readiness(mysql_config=None, connect_home=None, debezium_dir=None):
    # [문제 1 · 여러 줄] 세 선택 인수를 이름 있는 사전으로 모은다. (2줄)
    # 예시: inputs = {"source": source_path, "target": target_path,
    #                "archive": archive_path}
    supplied_paths = {
        "mysql_config":mysql_config,
        "connect_home":connect_home,
        "debezium_dir":debezium_dir,
        }

    
    # [문제 2 · 한 줄] 각 이름에 제공 여부와 존재 여부를 담는 사전 내포를 대입한다.
    # 예시: info = {name: {"supplied": bool(path), "exists": Path(path).exists() if path else False} for name, path in inputs.items()}
    paths = {name: 
                {"supplied": bool(value), 
                 "exists": Path(value).exists() if value else False } for name, value in supplied_paths.items()}

    return {"schema_version": "cdc-readiness/v1", "paths": paths,
            "mysql_binlog": "not-verified", "cdc_reader": "not-configured",
            "connect_worker": "not-configured", "debezium_connector": "not-configured",
            "player_change_topic": "not-configured", "common_input": SCHEMA_VERSION,
            # [문제 3 · 한 단어] 실제 CDC 원문을 관찰하지 않은 상태의 bool이다.
            # 힌트 3: 경로 존재 여부와 달리 이 함수에서 실행 증거를 얻지 않는다.
            "binlog_cdc_observed": False}


def change_player(event):
    # [문제 1 · 여러 줄] teaching-fixture 이외의 출처는 거절한다. (2줄)
    # 예시: if item.get("kind") != "sample":
    #           raise ValueError("sample만 받습니다.")
    if event.get("source_kind") != "teaching-fixture":
        raise ValueError("teaching-fixture 출처만 처리 가능.")

    op = event.get("op")
    before, after = event.get("before"), event.get("after")
    if op == "r":
        if before is not None or not isinstance(after, dict):
            raise ValueError("r은 before=None과 after 공개 상태가 필요합니다.")
        _check_public_state(after)
    elif op == "u":
        _check_public_state(before)
        _check_public_state(after)
        # [문제 2 · 한 단어] 수정 전후 ID가 다르면 오류로 들어간다.
        if before["id"] != after["id"]:
            raise ValueError("u의 before와 after id가 다릅니다.")
    elif op == "d":
        if not isinstance(before, dict) or after is not None:
            raise ValueError("d는 before 공개 상태와 after=None이 필요합니다.")
        _check_public_state(before)
    else:
        raise ValueError("op는 r, u, d만 받습니다.")
    # [문제 3 · 한 줄] d는 before, r/u는 after를 state에 담는다.
    # 예시: selected = old if mode == "previous" else new
    state = before if op == "d" else after

    # [문제 4 · 여러 줄] 공개 상태와 삭제 여부를 새 사전으로 반환한다. (2줄)
    # 예시: return {"kind": kind, "item_id": selected["id"],
    #               "removed": kind == "remove"}
    return {"op":op, "player_id":state["id"], "coins": state["coins"],
            "version": state["version"], "deleted":op == "d"}

def build_snapshot_contract(source):
    # [문제 1 · 한 줄] source를 검사한 결과를 inspected에 담는다.
    # 예시: checked = inspect_snapshot(input_path)
    inspected = inspect_snapshot(source)
    # [문제 2 · 여러 줄] 위 계약 표의 안정 메타데이터를 contract 사전으로 만든다. (5줄)
    # 예시: metadata = {"artifact_id": "sample.ndjson",
    #                  "source_path": str(input_path), "fields": list(names)}
    contract = {
        "artifact_id": "game_server/data/exports/player-cdc.ndjson", "artifact_version": "v2",
        "source_path": str(source), "created_at": datetime.now(timezone.utc).isoformat(),
        "collector": "game.export_player_snapshot", "binlog_cdc_status": "not-configured",
        "position_kind": "file-line", "kafka_position": None,
        "public_field": list(PUBLIC_FIELDS)
    }

    # [문제 3 · 한 단어] 실제 검사 결과의 키·값을 contract에 합친다.
    contract.update(inspected)
    return contract

def load_rows(path):
    inspect_snapshot(path)
    return {row["id"]: row for row in read_ndjson(path)}

def compare(before, after):
    changed = []
    for player_id in sorted(set(before) & set(after)):
        # [문제 1 · 한 줄] 같은 player_id의 이전·이후 행을 old와 new에 담는다.
        # 예시: left, right = earlier[code], later[code]
        old, new = before[player_id], after[player_id]

        # [문제 2 · 여러 줄] 업무 필드와 UTC 수정 시각으로 전후 튜플을 만든다. (2줄)
        # 예시: left_state = (left["title"], parse_utc(left["when"]))
        #       right_state = (right["title"], parse_utc(right["when"]))
        old_state = (old["room_id"], old["coins"], old["version"], parse_utc(old["updated_at"]))
        new_state = (new["room_id"], new["coins"], new["version"], parse_utc(new["updated_at"]))


        # [문제 3 · 한 단어] 전후 업무 상태가 다르면 변경 행을 만든다.
        if old_state != new_state:
            # [문제 4 · 여러 줄] ID와 전후 version·coins를 changed에 추가한다. (3줄)
            # 예시: output.append({"code": code, "old_value": left["value"],
            #                      "new_value": right["value"]})
            changed.append({"id": player_id, "before_version": old["version"],
                            "after_version": new["version"], "before_coins": old["coins"],
                            "after_coins": new["coins"]})
    return {"changed": changed, "newly_seen": sorted(set(after) - set(before)),
            "missing_unknown": sorted(set(before) - set(after))}


def missing_summary(before, after):
    # [문제 1 · 한 줄] before에만 남은 ID를 정렬해 missing에 담는다.
    # 예시: missing_codes = sorted(set(old_codes) - set(new_codes))
    missing = sorted(set(before) - set(after))

    # [문제 2 · 여러 줄] 누락 ID·비교 출처·빈 삭제 목록·삭제 추론 불가를 result에 구성한다. (2줄)
    # 예시: result = {"unknown": missing_codes,
    #                "source_kind": "file-comparison", "actions": [],
    #                "action_allowed": False}
    result = {"unknown": missing,
        "source_kind": "snapshot-comparison", "delete_events": [],
        "delete_inference_allowed": False}
    
    return result


def handoff_snapshot(source, contract_path, target):
    source, target = Path(source), Path(target)
    contract = json.loads(Path(contract_path).read_text(encoding="utf-8"))
    inspected = inspect_snapshot(source)
    expected = {"artifact_id": "data/exports/player-cdc.ndjson", "artifact_version": "v2",
                "public_fields": list(PUBLIC_FIELDS), "position_kind": "file-line",
                "kafka_position": None, "collector": "game.export_player_snapshot",
                "binlog_cdc_status": "not-configured", **inspected}
    # [문제 1 · 여러 줄] 검사한 원본의 기대 필드를 계약과 JSON 형태로 대조하고 누락·값/타입 불일치를 거절한다. (3줄)
    # 예시: for name, value in required.items():
    #           if name not in supplied or json.dumps(supplied[name], sort_keys=True) != json.dumps(value, sort_keys=True):
    #               raise ValueError(f"다른 값: {name}")
    for field, value in expected.items():
        if field not in contract or contract[field] != value:
            raise ValueError(f"계약과 실 데이터가 다릅니다: {field}")

    parse_utc(contract["created_at"])
    # [문제 2 · 여러 줄] 기존 수신 폴더가 있으면 덮어쓰기 전에 거절한다. (2줄)
    # 예시: if output_path.exists():
    #           raise ValueError("새 출력 경로를 지정하세요.")
    if target.exists():
        raise ValueError("이미 존재하는 경로/파일입니다.")

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{target.name}-", dir=target.parent))
    try:
        received = temporary / "player-cdc.ndjson"
        # [문제 3 · 여러 줄] 원본을 임시 수신 파일로 복사하고 그 bytes의 checksum을 대조한다. (3줄)
        # 예시: shutil.copyfile(input_path, copied_path)
        #        if hashlib.sha256(copied_path.read_bytes()).hexdigest() != expected_hash:
        #            raise ValueError("복사 결과가 다릅니다.")
        shutil.copyfile(source, received)
        if hashlib.sha256(received.read_bytes()).hexdigest() != inspected["sha256"]:
            raise ValueError("복사 결과가 다릅니다.")
        
        # [문제 4 · 한 줄] 기존 계약을 복사하되 source_path만 최종 수신 파일 경로로 바꾼다.
        # 예시: copied_metadata = {**metadata, "path": str(output_path)}
        received_contract = {**contract, "source_path": str(target / "player-cdc.ndjson")}

        (temporary / "player-cdc-contract.json").write_text(
            json.dumps(received_contract, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8")
        
        # [문제 5 · 한 줄] 검증된 파일·계약이 모두 준비된 임시 폴더를 최종 target으로 옮긴다.
        # 예시: staged_folder.rename(final_folder)
        temporary.rename(target)
        
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {"rows": inspected["rows"], "sha256": inspected["sha256"],
            "source_kind": SOURCE_KIND, "target": str(target)}