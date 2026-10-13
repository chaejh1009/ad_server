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
from pymongo.errors import DuplicateKeyError
from .mongo import get_db

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

def normalize_snapshot_file(source, contract_path, output, media_id="village-game"):
    if not isinstance(media_id, str) or not media_id.strip():
        raise ValueError("media_id는 비어 있지 않은 문자열이어야 합니다.")
    target = Path(output)
    if target.resolve() in {Path(source).resolve(), Path(contract_path).resolve()}:
        raise ValueError("출력은 원본·계약과 다른 경로여야 합니다.")
    rows, inspected = read_snapshot_package(source, contract_path)
    # [문제 1 · 여러 줄] 모든 행을 변환하고 서로 다른 change_id 개수를 센다. (2줄)
    # 예시: packets = [convert(item, group_id=group_id) for item in entries]
    #       unique_codes = len({packet["code"] for packet in packets})
    changes = [normalize_snapshot(row, media_id=media_id) for row in rows]
    unique_ids = len({change["change_id"] for change in changes})    

    if unique_ids != len(changes):
        raise ValueError("정규화 change_id가 중복됐습니다.")
    target.parent.mkdir(parents=True, exist_ok=True)
    # 모두 변환한 뒤 임시 파일에 쓰고, 완성된 파일만 최종 경로로 옮긴다.
    with tempfile.TemporaryDirectory(prefix=".normalize-", dir=target.parent) as folder:
        staged = Path(folder) / "changes.ndjson"
        # [문제 2 · 한 줄] 임시 경로에 모든 변경을 쓰고 반환 SHA를 checksum에 담는다.
        # 예시: digest = write_ndjson(temporary_file, packets)
        checksum = write_ndjson(staged, changes)

        # [문제 3 · 한 단어] 완성된 임시 파일을 최종 경로로 교체하는 os 함수다.
        # 힌트 3: 24일차 export처럼 파일 작성이 끝난 뒤 목적지를 교체한다.
        os.replace(staged, target)
    return {"path": str(target), "rows": len(changes), "sha256": checksum,
            "schema_version": "player-context-change/v1", "source_kind": SOURCE_KIND,
            "source_sha256": inspected["sha256"], "media_id": media_id,
            "op_counts": {"upsert": len(changes)}, "unique_change_ids": unique_ids,
            "preview": changes[:1]}

def context_subject_key(media_id, subject_id):
    """매체와 공개 대상을 구분하는 안정 키를 만든다."""
    for name, value in (("media_id", media_id), ("subject_id", subject_id)):
        if not isinstance(value, str) or not value.strip() or ":" in value:
            raise ValueError(f"{name}는 콜론 없는 비어 있지 않은 문자열이어야 합니다.")
    return media_id + ":" + subject_id


def _check_context_change(change):
    """정규화 계약을 대조한다. 파일이나 MongoDB를 변경하지 않는다."""
    fields = {"schema_version", "source_kind", "media_id", "subject_id", "op",
              "version", "event_time", "context", "change_id"}
    if not isinstance(change, dict) or set(change) != fields:
        raise ValueError("context 변경은 정해진 9개 필드만 받습니다.")
    if change["schema_version"] != "player-context-change/v1":
        raise ValueError("player-context-change/v1 입력이 필요합니다.")
    if change["source_kind"] not in {"player-snapshot", "teaching-fixture"}:
        raise ValueError("source_kind는 player-snapshot 또는 teaching-fixture입니다.")
    if change["op"] not in {"upsert", "delete"}:
        raise ValueError("op는 upsert 또는 delete입니다.")
    context_subject_key(change["media_id"], change["subject_id"])
    subject = change["subject_id"]
    if change["source_kind"] == "player-snapshot":
        if not subject.isascii() or not subject.isdecimal() or int(subject) <= 0 or str(int(subject)) != subject:
            raise ValueError("player-snapshot의 subject_id는 양의 공개 ID를 그대로 바꾼 문자열입니다.")
        if change["op"] != "upsert":
            raise ValueError("player-snapshot은 upsert만 허용합니다.")
    elif not subject.startswith("fixture-") or subject == "fixture-":
        raise ValueError("teaching-fixture는 fixture-로 시작하는 별도 subject가 필요합니다.")
    if type(change["version"]) is not int or change["version"] < 0:
        raise ValueError("version은 0 이상 정수입니다.")
    instant = parse_utc(change["event_time"])
    if instant.isoformat() != change["event_time"]:
        raise ValueError("event_time은 UTC로 정규화한 ISO 시각이어야 합니다.")
    context = change["context"]
    if not isinstance(context, dict):
        raise ValueError("context는 사전이어야 합니다.")
    if change["op"] == "delete":
        if context:
            raise ValueError("delete의 context는 빈 사전이어야 합니다.")
    else:
        if set(context) != {"player_id", "room_id", "coins", "version", "updated_at"}:
            raise ValueError("upsert context는 정해진 5개 공개 필드만 받습니다.")
        if context["player_id"] != subject:
            raise ValueError("context.player_id와 subject_id가 다릅니다.")
        if type(context["version"]) is not int or context["version"] != change["version"]:
            raise ValueError("context.version과 version이 다릅니다.")
        if not isinstance(context["room_id"], str) or type(context["coins"]) is not int:
            raise ValueError("room_id는 문자열, coins는 정수여야 합니다.")
        parse_utc(context["updated_at"])
        if context["updated_at"] != change["event_time"]:
            raise ValueError("context.updated_at과 event_time이 다릅니다.")
    body = {name: value for name, value in change.items() if name != "change_id"}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    expected_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if change["change_id"] != expected_id:
        raise ValueError("change_id와 정규화 내용이 다릅니다.")


def make_context_document(change):
    """검증한 변경 한 행을 저장할 문서로 바꾼다. 아직 저장하지 않는다."""
    _check_context_change(change)
    # [문제 1 · 한 줄] 두 ID로 안정 키를 만들고 key에 담는다.
    # 예시: code = compose_key(packet["group_id"], packet["member_id"])
    key = context_subject_key(change["media_id"], change["subject_id"])

    # [문제 2 · 여러 줄] 여섯 입력 필드를 document에 복사하고 저장 전용 세 필드를 추가한다. (4줄)
    # 결과: media_id, subject_id, version, source_kind, change_id, event_time,
    #       _id, deleted, context를 갖는 사전.
    # 예시: record = {name: packet[name] for name in ("group_id", "revision")}
    #       record.update({"_id": code, "inactive": packet["action"] == "stop",
    #                      "payload": {} if packet["action"] == "stop" else dict(packet["payload"])})
    record = {name: change[name] for name in ("media_id", "subject_id", "version", "source_kind", "change_id", "event_time")}
    record.update({"_id": key, "deleted": change["op"] == "delete",
                    "context": {} if change["op"] == "deleted" else dict(change["context"])})

    # [문제 3 · 한 단어] 방금 구성한 저장 문서를 호출자에게 반환한다.
    # 힌트 3: 입력 change가 아니라 새로 만든 사전의 변수명이다.
    return record

def apply_context(change):
    document = make_context_document(change)
    key = document["_id"]
    collection = get_db().player_context
    # 먼저 읽은 상태가 여전히 맞을 때만 저장한다. 경쟁하면 다시 읽는다.
    for attempt in range(3):
        old = collection.find_one({"_id": key})
        if old is None:
            try:
                collection.insert_one(document)
                return "applied"
            except DuplicateKeyError:
                continue
        # [문제 1 · 여러 줄] 현재가 더 큰 version이면 오래된 입력을 반환한다. (2줄)
        # 예시: if current["rank"] > packet["rank"]:
        #           return "older"
        if old["version"] > document["version"]:
            return "stale"

        if old["version"] == document["version"]:
            # [문제 2 · 한 줄] 삭제 표시와 공개 context가 모두 같은 경우만 분기한다.
            # 예시: if current["closed"] == packet["closed"] and current["detail"] == packet["detail"]:
            if old["deleted"] == document["deleted"] and old["context"] == document["context"]:
                return "duplicate"
            raise ValueError("version_conflict: 같은 version의 상태가 다릅니다.")
        # [문제 3 · 한 줄] 읽은 이전 version이 아직 맞을 때만 document로 교체한다.
        # 예시: result = records.replace_one({"_id": code, "rank": current["rank"]}, packet)
        result = collection.replace_one({"_id": key, "version": old["version"]}, document)

        # [문제 4 · 한 단어] 교체 필터와 일치한 문서 수를 읽는 속성이다.
        # 힌트 4: 앞에서 설명한 UpdateResult의 필터 일치 수다.
        if result.matched_count == 1:
            return "applied"
    raise ValueError("concurrent_update: 최신 상태를 다시 읽고 재시도하세요.")

def get_context(media_id, subject_id):
    key = context_subject_key(media_id, subject_id)
    row = get_db().player_context.find_one({"_id": key})
    return dict(row["context"]) if row and not row["deleted"] else {}

def _read_context_changes(source):
    """같은 bytes에서 SHA와 검증한 정규화 행을 함께 얻는다."""
    payload = Path(source).read_bytes()
    rows = []
    for number, line in enumerate(payload.splitlines(), 1):
        if not line.strip():
            raise ValueError(f"빈 행 {number}")
        row = json.loads(line.decode("utf-8"))
        make_context_document(row)
        rows.append(row)
    return rows, hashlib.sha256(payload).hexdigest()


def _read_context_checkpoint(checkpoint, checksum, row_count):
    state = json.loads(Path(checkpoint).read_text(encoding="utf-8"))
    fields = {"schema_version", "source_sha256", "next_line"}
    if not isinstance(state, dict) or set(state) != fields:
        raise ValueError("checkpoint는 정해진 3개 필드만 받습니다.")
    if state["schema_version"] != "context-checkpoint/v1":
        raise ValueError("checkpoint 버전이 다릅니다.")
    digest = state["source_sha256"]
    if (not isinstance(digest, str) or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)):
        raise ValueError("checkpoint의 source_sha256이 잘못되었습니다.")
    if digest != checksum:
        raise ValueError("입력 파일이 바뀌었습니다. 새 checkpoint를 사용하세요.")
    position = state["next_line"]
    if type(position) is not int or not 0 <= position <= row_count:
        raise ValueError("checkpoint의 다음 행이 잘못되었습니다.")
    return position


def _save_context_checkpoint(checkpoint, checksum, position):
    """완성된 임시 파일로만 위치 기록을 교체한다."""
    target = Path(checkpoint)
    target.parent.mkdir(parents=True, exist_ok=True)
    state = {"schema_version": "context-checkpoint/v1",
             "source_sha256": checksum, "next_line": position}
    with tempfile.TemporaryDirectory(prefix=".checkpoint-", dir=target.parent) as folder:
        staged = Path(folder) / "state.json"
        staged.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
        os.replace(staged, target)
    return state

def project_context_file(source_path, checkpoint_path=None, limit=None):
    if limit is not None and (type(limit) is not int or limit < 1):
        raise ValueError("limit은 양수 정수입니다.")
    source = Path(source_path)
    if checkpoint_path is not None and not str(checkpoint_path).strip():
        raise ValueError("checkpoint 경로는 비어 있지 않아야 합니다.")
    checkpoint = Path(checkpoint_path) if checkpoint_path is not None else None
    if checkpoint is not None:
        if (source.resolve() == checkpoint.resolve()
                or (source.exists() and checkpoint.exists() and source.samefile(checkpoint))):
            raise ValueError("checkpoint는 원본 입력과 다른 파일이어야 합니다.")
    # [문제 1 · 한 줄] 같은 bytes의 검증된 모든 행과 SHA를 함께 읽는다.
    # 예시: entries, digest = read_verified_file(input_path)
    rows, checksum = _read_context_changes(source)
    position = 0
    state = None
    # [문제 2 · 여러 줄] 기존 checkpoint가 있을 때 검사한 위치와 그 상태를 복원한다. (4줄)
    # 예시: if marker is not None and marker.exists():
    #           index = read_marker(marker, digest, len(entries))
    #           saved = {"schema": "sample/v1",
    #                    "hash": digest, "next": index}
    if checkpoint is not None and checkpoint.exists():
        position = _read_context_checkpoint(checkpoint, checksum, len(rows))
        state = {"schema_version": "context-checkpoint/v1",
                    "source_sha256": checksum, "next_line": position}

    start = position
    counts = {"applied": 0, "duplicate": 0, "stale": 0}
    stop = min(len(rows), position + limit) if limit is not None else len(rows)
    while position < stop:
        # [문제 3 · 한 줄] 현재 index의 입력을 4교시 함수로 반영하고 결과를 받는다.
        # 예시: result = apply_record(entries[index])
        status = apply_context(rows[position])

        if status not in counts:
            raise ValueError("알 수 없는 반영 결과입니다.")
        # [문제 4 · 여러 줄] 반영 성공 후에만 다음 위치를 저장하고 이동한다. (4줄)
        # 예시: following = index + 1
        #       if marker is not None:
        #           saved = save_marker(marker, digest, following)
        #       index = following
        next_position = position + 1
        if checkpoint is not None:
            state = _save_context_checkpoint(checkpoint, checksum, next_position)
            position = next_position

        # [문제 5 · 한 단어] 이번 행에서 받은 applied·duplicate·stale 중 하나다.
        # 힌트 5: 문제 3의 반환값을 담은 변수명이다.
        counts[status] += 1

    # 빈 입력도 next_line=0을 저장한다. 기존 완료 기록은 덮어쓰지 않는다.
    if checkpoint is not None and state is None:
        state = _save_context_checkpoint(checkpoint, checksum, position)
    return {"processed": position - start, "applied": counts["applied"],
            "skipped": counts["duplicate"] + counts["stale"], "counts": counts,
            "start_line": start, "next_line": position, "rows": len(rows),
            "done": position == len(rows), "source_sha256": checksum,
            "checkpoint_path": str(checkpoint) if checkpoint is not None else None,
            "checkpoint_state": state}

def refresh_snapshot(source, contract_path, media_id="village-game"):
    context_subject_key(media_id, "refresh")
    # [문제 1 · 여러 줄] 수신 계약을 대조한 행·검사 결과를 읽고 모든 행을 정규화한다. (2줄)
    # 예시: entries, checked = read_package(input_file, metadata_file)
    #       packets = [convert(entry, group_id=group_id) for entry in entries]
    rows, inspected = read_snapshot_package(source, contract_path)
    changes = [normalize_snapshot(row, media_id=media_id) for row in rows]

    counts = {"applied": 0, "duplicate": 0, "stale": 0}
    for change in changes:
        # [문제 2 · 한 줄] 현재 변경을 실제 반영 함수에 넘기고 상태를 status에 담는다.
        # 예시: result = apply_record(packet)
        status = apply_context(change)

        if status not in counts:
            raise ValueError("알 수 없는 반영 결과입니다.")
        # [문제 3 · 한 단어] 방금 반환된 상태의 수를 늘릴 변수명이다.
        # 힌트 3: 문제 2의 반환값이며 applied·duplicate·stale 중 하나다.
        counts[status] += 1
        
    return {"source": str(source), "contract": str(contract_path), "rows": len(rows),
            "source_sha256": inspected["sha256"], "media_id": media_id,
            "counts": counts, "preview": changes[:1]}