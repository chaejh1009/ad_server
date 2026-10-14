import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from .exporting import read_ndjson
from .context_projection import make_context_document, _read_context_changes


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

def write_ndjson(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(stable_json(row) + "\n")

def build_lake_version(source_path, output_dir):
    source = Path(source_path)
    output = Path(output_dir)
    # [문제 1 · 여러 줄] 같은 bytes의 행·SHA를 받고 history→current를 만든다. (3줄)
    # 예시: entries, digest = read_valid_file(input_path)
    #       steps = make_steps(entries)
    #       latest = select_latest(steps)
    source_rows, source_checksum = _read_context_changes(source)
    history = build_history(source_rows)
    current = build_current(history)

    # 이전 버전을 덮어쓰지 않고 새 디렉터리에 결과를 쓴다.
    # [문제 2 · 한 줄] 기존 run을 거절하는 새 디렉터리를 만든다.
    # 예시: folder.mkdir(parents=True, exist_ok=False)
    output.mkdir(parents=True, exist_ok=False)

    files = {}
    for name, rows in (("history", history), ("current", current)):
        # [문제 3 · 여러 줄] 결과 파일 쓰기·행 수·파일 bytes SHA를 연결한다. (4줄)
        # 예시: saved = folder / (label + ".ndjson")
        #       save_records(saved, entries)
        #       evidence[label] = {"path": saved.name, "rows": len(entries),
        #                          "sha256": hashlib.sha256(saved.read_bytes()).hexdigest()}
        path = output / (name + ".ndjson")
        write_ndjson(path, rows)
        files[name] = {"path": path.name, "rows": len(rows),
                            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    # [문제 4 · 한 단어] 같은 원본의 SHA를 받은 변수다.
    manifest = {
        "schema_version": "player-lake/v1", "source_kind": "player-context-change",
        "source_path": str(source), "source_sha256": source_checksum,
        "input_rows": len(source_rows), "history_rows": len(history), "current_rows": len(current),
        "source_max_event_time": history[-1]["event_time"] if history else None,
        "output_dir": str(output), "files": files,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # manifest가 없는 디렉터리는 완성 버전으로 소비하지 않는다.
    # [문제 5 · 여러 줄] manifest를 UTF-8 JSON 파일로 마지막에 기록한다. (2줄)
    # 예시: (folder / "summary.json").write_text(
    #           json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return manifest