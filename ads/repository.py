from pymongo.errors import DuplicateKeyError

from .mongo import get_db


# 기존 캠페인의 소유자를 검사하고 생성 시각은 최초 저장 때만 설정한다.
def save_campaign_document(document):
    db = get_db()
    campaign_id = document["campaign_id"]
    owner_user_id = document["owner_user_id"]
    # 예시: previous = db.projects.find_one({"_id": project_id})
    # [문제 1 · 한 줄] campaign_id와 일치하는 기존 캠페인을 old로 읽는 한 줄을 작성해보세요.
    old = db.campaigns.find_one({"_id": campaign_id})
    # [문제 2 · 한 단어] 빈칸을 채워보세요.
    if old and old["owner_user_id"] != owner_user_id:
        raise ValueError("campaign_id already belongs to another user")
    # 예시: updates = {
    #           name: value for name, value in record.items() if name not in {"id", "opened_at"}
    #       }
    # [문제 3 · 여러 줄] document의 항목 중 _id와 created_at을 제외한 값만 changes 사전으로 모으는 코드를 작성해보세요. (5줄)
    changes = {
            key : value
            for key, value in document.items()
            if key not in {"_id", "created_at"}
        }

    # ID와 소유자 조건으로 갱신하거나 삽입하며 동시 생성의 중복 키도 오류로 처리한다.
    try:
        db.campaigns.update_one(
            {"_id": campaign_id, "owner_user_id": owner_user_id},
            {
                "$set": changes,
                # [문제 4 · 한 단어] 빈칸을 채워보세요.
                "$setOnInsert": {"created_at": document["created_at"]},
            },
            # [문제 5 · 한 단어] 빈칸을 채워보세요.
            upsert=True,
        )
    except DuplicateKeyError as exc:
        raise ValueError("campaign_id already exists") from exc
    return db.campaigns.find_one(
        {"_id": campaign_id, "owner_user_id": owner_user_id},
        {"_id": 0},
    )


# 해당 소유자의 캠페인만 ID 순서로 조회하고 내부 _id는 응답에서 제외한다.
def list_campaign_documents(owner_user_id):
    return list(
        get_db().campaigns.find(
            {"owner_user_id": owner_user_id},
            {"_id": 0},
        # [문제 6 · 한 단어] 빈칸을 채워보세요.
        ).sort("campaign_id", 1)
    )

# 같은 bid_id는 갱신하고 없으면 삽입해 캠페인별 입찰 문서 한 건을 유지한다.
def save_bid_document(document):
    # 예시: report_db = get_report_db()
    # [문제 1 · 한 줄] 광고 데이터베이스 객체를 가져와 db에 담는 한 줄을 작성해보세요.
    db = get_db()
    db.bids.update_one(
        # [문제 2 · 한 단어] 빈칸을 채워보세요.
        {"_id": document["bid_id"]},
        # [문제 3 · 한 단어] 빈칸을 채워보세요.
        {"$set": document},
        # [문제 4 · 한 단어] 빈칸을 채워보세요.
        upsert=True,
    )
    # 예시: return db.orders.find_one(
    #           {"_id": record["order_id"]}, {"_id": 0},
    #       )
    # [문제 5 · 여러 줄] 방금 저장한 bid_id로 입찰 한 건을 다시 읽고 내부 _id를 제외하여 반환하는 코드를 작성해보세요. (4줄)
    return db.orders.find_one(
            {"_id": document["bid_id"]}, 
            {"_id": 0},
        )


# 해당 소유자의 입찰만 캠페인 ID 순서로 조회한다.
def list_bid_documents(owner_user_id):
    return list(
        get_db().bids.find(
            # [문제 6 · 한 단어] 빈칸을 채워보세요.
            {"owner_user_id": owner_user_id},
            {"_id": 0},
        ).sort("campaign_id", 1)
    )

