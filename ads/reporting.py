import json
from datetime import datetime, timedelta, timezone
from .mongo import get_db
from .timestamps import parse_utc

SEOUL = timezone(timedelta(hours=9), name="Asia/Seoul")

def publish_reports(rows):
    count = 0
    for row in rows:
        if row.get("schema_version") != "ad-report/v1":
            raise ValueError("ad-report/v1 보고서가 필요합니다.")
        key = (row["owner_user_id"], row["campaign_id"], row["slot_id"], row["date"])
        expected_id = json.dumps(key, ensure_ascii=False, separators=(",", ":"))
        if row["_id"] != expected_id:
            raise ValueError("보고서 업무 키와 ID가 다릅니다.")
        get_db().ad_daily_reports.replace_one({"_id": row["_id"]}, row, upsert=True)
        count += 1
    return count


def list_reports(owner_user_id):
    return list(get_db().ad_daily_reports.find(
        {"owner_user_id": owner_user_id}, {"_id": 0}
    ).sort([("date", -1), ("campaign_id", 1), ("slot_id", 1)]))