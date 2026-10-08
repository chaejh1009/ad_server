from datetime import datetime, timezone
from pathlib import Path
from .mongo import get_db
from .exporting import EVENT_FIELDS, read_ndjson, write_ndjson


def deliver_events(output_path, limit=100):
    if type(limit) is not int or limit < 1:
        raise ValueError("limit은 양수 정수입니다.")
    target = Path(output_path)
    rows = read_ndjson(target) if target.exists() else []
    existing = {}
    for row in rows:
        previous = existing.get(row["event_id"])
        if previous is not None and previous != row:
            raise ValueError("전달 파일의 사건 ID 내용 충돌")
        existing[row["event_id"]] = row
    collection = get_db().ad_events
    pending_rows = list(collection.find({"file_delivered_at": {"$exists": False}})
                        .sort([("event_time", 1), ("event_id", 1)]).limit(limit))
    for event in pending_rows:
        public = {field: event[field] for field in EVENT_FIELDS}
        previous = existing.get(event["event_id"])
        if previous is not None and previous != public:
            raise ValueError("이미 전달된 ID의 내용 충돌")
        existing[event["event_id"]] = public
    # 파일 완성 후 표식: 중단되면 다음 실행이 기존 ID를 확인하고 표식을 보완한다.
    ordered = sorted(existing.values(), key=lambda row: (row["event_time"], row["event_id"]))
    temporary = target.with_name(target.name + ".tmp")
    write_ndjson(temporary, ordered)
    temporary.replace(target)
    delivered_at = datetime.now(timezone.utc).isoformat()
    for event in pending_rows:
        collection.update_one({"_id": event["_id"]},
                              {"$set": {"file_delivered_at": delivered_at}})
    return {"processed": len(pending_rows), "total": collection.count_documents({}),
            "pending": collection.count_documents({"file_delivered_at": {"$exists": False}})}