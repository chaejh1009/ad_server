import re
from datetime import datetime, timezone
from pathlib import PurePosixPath
from uuid import uuid4
from .repository import list_campaign_documents, save_campaign_document
from .mongo import get_db
from .repository import list_bid_documents, save_bid_document


# 광고 위치·입찰 상한·선택 정책 버전을 공통 기준으로 둔다.
MEDIA_SLOTS = {"village-game": {"village-board", "lobby-banner"}}
SLOTS = MEDIA_SLOTS["village-game"]
MAX_BID_UNITS = 10000
POLICY_VERSION = "highest-bid-v1"


# 매체 안의 공개 식별자를 검사하며 게임 ORM을 참조하지 않는다.
def clean_subject(value):
    if not isinstance(value, dict):
        raise ValueError("subject must be an object")
    media_id = value.get("media_id")
    subject_id = value.get("subject_id")
    if not isinstance(media_id, str) or media_id not in MEDIA_SLOTS:
        raise ValueError("unknown media_id")
    if not isinstance(subject_id, str) or not 1 <= len(subject_id) <= 128:
        raise ValueError("subject_id must be a nonempty string")
    return {"media_id": media_id, "subject_id": subject_id}


# 매체 서버가 공개 항목만 고르고 광고 서버는 작은 JSON 사전 형태를 검사한다.
def clean_context(value):
    if not isinstance(value, dict) or len(value) > 16:
        raise ValueError("context must be a small object")
    for key, item in value.items():
        if not isinstance(key, str) or not 1 <= len(key) <= 64:
            raise ValueError("invalid context key")
        if item is not None and type(item) not in {str, int, float, bool}:
            raise ValueError("context values must be scalars")
        if isinstance(item, str) and len(item) > 256:
            raise ValueError("context text is too long")
    return dict(value)


def utc_now():
    return datetime.now(timezone.utc)


# ID는 2~48자의 소문자·숫자·하이픈만 허용한다.
def clean_id(value, label):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,47}", value):
        raise ValueError(f"{label} must use 2-48 lowercase letters, digits or hyphens")
    return value


# 등록한 두 광고 위치 중 하나인지 검사한다.
def clean_slot(value, media_id="village-game"):
    if not isinstance(value, str) or value not in MEDIA_SLOTS.get(media_id, set()):
        raise ValueError("unknown slot_id")
    return value


# 광고 이미지는 지정한 로컬 정적 경로와 확장자로 제한한다.
# 상위 경로 이동·역슬래시·쿼리·fragment는 거부한다.
def clean_creative(value):
    if not isinstance(value, str):
        raise ValueError("creative_path must be a string")
    path = PurePosixPath(value)
    if not value.startswith("/static/ads/creatives/"):
        raise ValueError("creative_path must start with /static/ads/creatives/")
    if ".." in path.parts or "\\" in value or "?" in value or "#" in value:
        raise ValueError("creative_path must be a plain local static path")
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError("unsupported image extension")
    return value


# 제목·활성 여부를 검사하고 캠페인 ID를 정리한다.
def save_campaign(user, data):
    campaign_id = clean_id(data.get("campaign_id"), "campaign_id")
    title = data.get("title")
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 80:
        raise ValueError("title must contain 1-80 characters")
    active = data.get("active", True)
    if type(active) is not bool:
        raise ValueError("active must be true or false")

    # 소유자는 로그인 사용자로 확정하고 이미지·위치를 검증한 문서를 저장한다.
    now = utc_now()
    document = {
        "schema_version": 1,
        "campaign_id": campaign_id,
        "owner_user_id": user.pk,
        "title": title.strip(),
        "creative_path": clean_creative(data.get("creative_path")),
        "media_id": data.get("media_id", "village-game"),
        "slot_id": clean_slot(data.get("slot_id"), data.get("media_id", "village-game")),
        "active": active,
        "created_at": now,
        "updated_at": now,
    }
    return save_campaign_document(document)


# 조회 범위도 로그인 사용자의 캠페인으로 제한한다.
def list_campaigns(user):
    return list_campaign_documents(user.pk)


# 입찰은 bool을 제외한 1~10000 정수이며 본인 소유의 활성 캠페인만 허용한다.
def save_bid(user, data):
    campaign_id = clean_id(data.get("campaign_id"), "campaign_id")
    amount = data.get("bid_units")
    if type(amount) is not int or not 1 <= amount <= MAX_BID_UNITS:
        raise ValueError("bid_units must be an integer from 1 to 10000")
    campaign = get_db().campaigns.find_one({
        "_id": campaign_id,
        "owner_user_id": user.pk,
        "active": True,
    })
    if campaign is None:
        raise ValueError("active owned campaign was not found")

    # 광고 위치는 요청값 대신 캠페인에서 가져와 같은 ID의 입찰을 저장한다.
    document = {
        "schema_version": 1,
        "bid_id": campaign_id,
        "campaign_id": campaign_id,
        "owner_user_id": user.pk,
        "slot_id": campaign["slot_id"],
        "media_id": campaign["media_id"],
        "bid_units": amount,
        "active": True,
        "updated_at": utc_now(),
    }
    return save_bid_document(document)


# 로그인한 사용자의 입찰 목록만 반환한다.
def list_bids(user):
    return list_bid_documents(user.pk)

# 같은 광고 위치의 활성 캠페인과 입찰을 모은다.
def candidate_rows(slot_id, media_id="village-game"):
    db = get_db()
    campaigns = {
        row["campaign_id"]: row
        for row in db.campaigns.find({"active": True, "media_id": media_id, "slot_id": slot_id})
    }
    rows = []

    # 소유자가 일치하고 정수 입찰 범위를 지킨 후보만 광고 정보와 함께 남긴다.
    for bid in db.bids.find({"active": True, "media_id": media_id, "slot_id": slot_id}):
        campaign = campaigns.get(bid["campaign_id"])
        if campaign is None:
            continue
        if campaign["owner_user_id"] != bid["owner_user_id"]:
            continue
        amount = bid.get("bid_units")
        if type(amount) is not int or not 1 <= amount <= MAX_BID_UNITS:
            continue
        rows.append({
            "campaign_id": campaign["campaign_id"],
            "owner_user_id": campaign["owner_user_id"],
            "title": campaign["title"],
            "creative_path": campaign["creative_path"],
            "slot_id": slot_id,
            "bid_units": amount,
        })

    # 입찰이 높은 후보를 앞에 두고 동점은 캠페인 ID로 순서를 고정한다.
    return sorted(rows, key=lambda row: (-row["bid_units"], row["campaign_id"]))

# 매체가 확인한 subject와 요청 위치를 검사하고 후보가 없으면 빈 결과를 돌려준다.
def choose_ad(subject, slot_id, context):
    subject = clean_subject(subject)
    slot_id = clean_slot(slot_id, subject["media_id"])
    context = clean_context(context)
    # [문제 1 · 한 단어] 빈칸을 채워보세요.
    candidates = candidate_rows(slot_id, subject["media_id"])
    if not candidates:
        # 예시: return {
        #           "empty": True, "area_id": area_id, "rule_version": RULE_VERSION,
        #       }
        # [문제 2 · 여러 줄] 후보가 없을 때 empty=True와 요청 slot_id·정책 버전을 반환하는 코드를 작성해보세요. (5줄)
        return {
                "empty": True, "slot_id": slot_id, "rule_version": POLICY_VERSION,
            }

    # 최고 후보를 고르고 매체 서버가 전달한 공개 context를 선택 당시 문맥으로 보존한다.
    # 예시: winner = ranked_items[0]
    # [문제 3 · 한 줄] 정렬된 후보 목록에서 최고 후보 하나를 selected로 고르는 한 줄을 작성해보세요.
    selected = candidates[0]
    # [문제 4 · 한 단어] 빈칸을 채워보세요.
    decision_id = str(uuid4())
    selected_at = utc_now()

    # 화면에 보낼 광고 정보와 새 decision_id를 구성한다.
    response = {
        "empty": False,
        "decision_id": decision_id,
        "campaign_id": selected["campaign_id"],
        "title": selected["title"],
        "creative_path": selected["creative_path"],
        "slot_id": slot_id,
        "bid_units": selected["bid_units"],
        "policy_version": POLICY_VERSION,
    }

    # 응답·당시 후보·플레이어 문맥을 새 결정 문서로 보존한 뒤 응답한다.
    # [문제 5 · 한 단어] 빈칸을 채워보세요.
    get_db().decisions.insert_one({
        "_id": decision_id, "schema_version": 1, **response,
        "subject": subject, "media_id": subject["media_id"],
        "player_id": context.get("player_id"), "selected_at": selected_at,
        "event_time": selected_at.isoformat(),
        "owner_user_id": selected["owner_user_id"],
        "chosen_campaign_id": selected["campaign_id"],
        "chosen_bid_amount": selected["bid_units"],
        "creative": {"title": selected["title"], "body": ""},
        "candidates": [
            {"campaign_id": row["campaign_id"], "bid_units": row["bid_units"],
            "owner_user_id": row["owner_user_id"], "bid_amount": row["bid_units"]}
            for row in candidates
        ],
        "context": context,
    })
    return response