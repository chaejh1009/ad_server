"""선택 당시 스냅샷에서만 실제 표시·클릭 사건을 만든다."""
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError
from .mongo import get_db
from .services import clean_subject


def record_ad_event(subject, decision_id, event_type):
    subject = clean_subject(subject)
    if not isinstance(decision_id, str) or not decision_id:
        raise ValueError("decision_id_required")
    if event_type not in {"impression", "click"}:
        raise ValueError("event_type_invalid")
    db = get_db()
    # 내장 문서는 전체 문서의 필드 순서 대신 각 식별자로 비교한다.
    decision = db.decisions.find_one({
        "_id": decision_id,
        "subject.media_id": subject["media_id"],
        "subject.subject_id": subject["subject_id"],
    })
    if decision is None:
        raise ValueError("decision_not_found_for_subject")
    campaign_id = decision.get("chosen_campaign_id")
    candidates = decision.get("candidates")
    if not campaign_id or not isinstance(candidates, list):
        raise ValueError("decision_snapshot_missing: 광고를 새로 요청하세요.")
    chosen = next((row for row in candidates if isinstance(row, dict)
                   and row.get("campaign_id") == campaign_id), None)
    if (chosen is None or type(chosen.get("owner_user_id")) is not int
            or type(chosen.get("bid_amount")) is not int
            or chosen["bid_amount"] < 1
            or not isinstance(decision.get("slot_id"), str)):
        raise ValueError("decision_snapshot_missing: 광고를 새로 요청하세요.")
    event_id = decision_id + ":" + event_type
    impression = db.ad_events.find_one({"_id": decision_id + ":impression"})
    if event_type == "click" and impression is None:
        raise ValueError("impression_required")
    now = datetime.now(timezone.utc).isoformat()
    document = {
        "_id": event_id, "schema_version": "ad-event/v1",
        "event_id": event_id, "decision_id": decision_id,
        "event_type": event_type, "event_time": now,
        "impression_time": impression["event_time"] if event_type == "click" else now,
        "media_id": subject["media_id"], "subject": subject,
        "slot_id": decision["slot_id"], "campaign_id": campaign_id,
        "owner_user_id": chosen["owner_user_id"], "bid_amount": chosen["bid_amount"],
    }
    try:
        result = db.ad_events.update_one(
            {"_id": event_id}, {"$setOnInsert": document}, upsert=True)
        created = result.upserted_id is not None
    except DuplicateKeyError:
        created = False
    return {"event_id": event_id, "event_type": event_type, "created": created}