import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from .exporting import read_ndjson
from .context_projection import make_context_document

def stable_json(row):
    return json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_history(rows):
    unique = {}
    for row in rows:
        if row.get("schema_version") != "player-context-change/v1":
            raise ValueError("normalized change schema required")
        if row.get("op") not in ("upsert", "delete"):
            raise ValueError("unknown operation")
        if type(row.get("version")) is not int or row["version"] < 0:
            raise ValueError("nonnegative integer version required")
        if not isinstance(row.get("context"), dict):
            raise ValueError("context object required")
        for field in ("change_id", "media_id", "subject_id", "event_time", "source_kind"):
            if not isinstance(row.get(field), str) or not row[field]:
                raise ValueError(f"missing {field}")
        when = datetime.fromisoformat(row["event_time"].replace("Z", "+00:00"))
        if when.tzinfo is None:
            raise ValueError("timezone required")
        old = unique.get(row["change_id"])
        if old is not None and stable_json(old) != stable_json(row):
            raise ValueError("same change_id has conflicting content")
        unique[row["change_id"]] = row
    return sorted(unique.values(), key=lambda row: (
        datetime.fromisoformat(row["event_time"].replace("Z", "+00:00")), row["change_id"]))

def build_current(history):
    """수신자별 최대 version을 고른다. 삭제 상태도 최신 후보에 남긴다."""
    current = {}
    ordered = sorted(build_history(history), key=lambda row: (
        row["media_id"], row["subject_id"], row["version"], row["change_id"]))
    for row in ordered:
        # [문제 1 · 여러 줄] 공개 문서와 안정 키, Lake 후보를 만든다. (3줄)
        # 예시: record = make_record(item)
        #       code = record["code"]
        #       selected = {"kind": "example/v1", **record}
        document = make_context_document(row)
        key = document["_id"]
        candidate = {"schema_version": "player-current/v1", **document}

        # [문제 2 · 한 줄] 같은 수신자의 이전 후보를 읽는다.
        # 예시: previous = by_code.get(code)
        old = current.get(key)

        # [문제 3 · 여러 줄] 처음 보거나 더 큰 version일 때 후보를 교체한다. (2줄)
        # 예시: if previous is None or selected["rank"] > previous["rank"]:
        #           by_code[code] = selected
        if old is None or candidate["version"] > old["version"]:
            current[key] = candidate

        # [문제 4 · 여러 줄] 같은 version의 다른 삭제·공개 상태를 거절한다. (3줄)
        # 예시: elif selected["rank"] == previous["rank"] and (
        #               selected["flag"] != previous["flag"] or selected["value"] != previous["value"]):
        #           raise ValueError("rank conflict")
        elif candidate["version"] == old["version"] and (
            candidate["deleted"] != old["deleted"] or candidate["context"] != old["context"]):
            raise ValueError("same version / conflict context")

    # [문제 5 · 한 단어] 후보 키를 고정 순서로 나열하는 함수다.
    return [current[key] for key in sorted(current)]