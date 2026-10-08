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

def build_daily_reports(events, generated_at=None):
    generated = parse_utc(generated_at) if generated_at else datetime.now(timezone.utc)
    unique, groups = {}, {}
    # 같은 사건 재전달을 제거하고 내용이 달라진 같은 ID는 거절한다.
    for event in events:
        event_id = event["event_id"]
        if event.get("schema_version") != "ad-event/v1":
            raise ValueError("ad-event/v1 입력이 필요합니다.")
        # [문제 1 · 여러 줄] 같은 ID의 다른 내용은 거절하고 사건을 unique에 보관한다. (4줄)
        # 예시: previous = by_id.get(item_id)
        #       if previous is not None and previous != item:
        #           raise ValueError("항목 내용 충돌")
        #       by_id[item_id] = item
        previous = unique.get(event_id)
        if previous is not None and previous != event:
            raise ValueError("event_id 충돌")
        unique[event_id] = event


    # 클릭은 노출일 cohort에 귀속한다. 고정 파일에 선행 노출이 없으면 오류다.
    for event in unique.values():
        if event["event_id"] != event["decision_id"] + ":" + event["event_type"]:
            raise ValueError("결정·종류와 사건 ID가 다릅니다.")
        if event["event_type"] == "impression" and parse_utc(event["impression_time"]) != parse_utc(event["event_time"]):
            raise ValueError("노출 사건의 기준 시각이 다릅니다.")
        if event["event_type"] == "click":
            # [문제 2 · 여러 줄] 같은 결정의 노출을 조회하고 없으면 거절한다. (3줄)
            # 예시: parent = records.get(parent_id)
            #       if parent is None:
            #           raise ValueError("부모 항목 없음")
            impression = unique.get(event["decision_id"] + ":" + "impression")
            if impression is None:
                raise ValueError("클릭 이전 노출이 없습니다.")
            same = ("subject", "campaign_id", "owner_user_id", "slot_id", "bid_amount")
            if any(event[name] != impression[name] for name in same):
                raise ValueError("클릭과 선행 노출의 업무 값이 다릅니다.")
            if parse_utc(event["impression_time"]) != parse_utc(impression["event_time"]):
                raise ValueError("클릭의 노출 기준 시각이 다릅니다.")
    for event in unique.values():
        instant = parse_utc(event["event_time"])
        impression_time = parse_utc(event["impression_time"])
        # [문제 3 · 한 줄] 노출 시각을 서울 달력 날짜의 ISO 문자열로 바꾼다.
        # 예시: local_day = stamp.astimezone(local_zone).date().isoformat()
        day = impression_time.astimezone(SEOUL).date().isoformat()
        key = (event["owner_user_id"], event["campaign_id"], event["slot_id"], day)
        # [문제 4 · 한 단어] 키가 있으면 기존 누적 행, 없으면 기본 행을 등록하는 사전 메서드다.
        row = groups.setdefault(key, {
            "_id": json.dumps(key, ensure_ascii=False, separators=(",", ":")),
            "schema_version": "ad-report/v1",
            "owner_user_id": key[0], "campaign_id": key[1], "slot_id": key[2], "date": day,
            "impressions": 0, "clicks": 0, "bid_units_sum": 0,
            "generated_at": generated.isoformat(),
            "source_max_event_time": instant.isoformat(),
        })
        if instant > parse_utc(row["source_max_event_time"]):
            row["source_max_event_time"] = instant.isoformat()
        # [문제 5 · 여러 줄] 노출·클릭을 따로 세고 포인트는 노출에만 더한다. (7줄)
        # 예시: if item["kind"] == "sale":
        #           total["sales"] += 1
        #           total["units"] += item["units"]
        #       elif item["kind"] == "return":
        #           total["returns"] += 1
        #       else:
        #           raise ValueError("알 수 없는 종류")
        if event["event_type"] == "impression":
            row["impressions"] += 1
            row["bid_units_sum"] += event["bid_amount"]
        elif event["event_type"] == "click":
            row["clicks"] += 1
        else:
            raise ValueError("알 수 없는 사건 종류")
    for row in groups.values():
        # [문제 6 · 한 줄] 클릭 수/노출 수를 기록하고 노출이 0이면 0.0으로 둔다.
        # 예시: item["rate"] = item["passed"] / item["tried"] if item["tried"] else 0.0
        row["ctr"] = row["clicks"] / row["impressions"] if row["impressions"] else 0.0
    return sorted(groups.values(), key=lambda row: row["_id"])
