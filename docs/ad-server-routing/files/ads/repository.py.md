# `ads/repository.py`

원본 소스 경로: `ads/repository.py` · 광고 작업 폴더 기준. [전체 라우팅](../../README.md)

## 책임과 경계

캠페인·입찰 문서의 PyMongo 저장·목록 조회를 담당한다. request·User 객체 대신 문서 또는 owner_user_id를 받는다.

## 호출자와 직접 의존

services.save_campaign/list_campaigns/save_bid/list_bids.

관련 문서: [ads/mongo.py](mongo.py.md), [ads/services.py](services.py.md).

## `def save_campaign_document(document)`

Signature: `def save_campaign_document(document)` · 소스 7행.

1. **검증·변환:** document의 campaign_id·owner_user_id를 읽고 같은 _id의 기존 캠페인을 조회한다. 기존 소유자가 다르면 ValueError다. 갱신값에서 _id·created_at을 제외한다.
2. **직접 호출:** `get_db()` → campaigns.find_one(_id) → campaigns.update_one(_id+owner, $set, $setOnInsert.created_at, upsert=True) → campaigns.find_one(_id+owner, {_id:0}).
3. **반환·상태:** 최초 created_at을 유지하며 저장한 캠페인 dict(내부 _id 제외)를 반환한다. 동시 생성 DuplicateKeyError는 ValueError("campaign_id already exists")로 바꾼다.

## `def list_campaign_documents(owner_user_id)`

Signature: `def list_campaign_documents(owner_user_id)` · 소스 48행.

1. **검증·변환:** owner_user_id를 조회 조건으로 사용한다. 추가 사용자 인증이나 타입 검증은 services/view에서 책임진다.
2. **직접 호출:** `get_db().campaigns.find({owner_user_id: ...}, {_id:0}).sort("campaign_id", 1)` → list.
3. **반환·상태:** 해당 소유자의 캠페인을 ID 오름차순 목록으로 반환한다.

## `def save_bid_document(document)`

Signature: `def save_bid_document(document)` · 소스 58행.

1. **검증·변환:** document["bid_id"]를 _id로 사용한다. 이 함수 안에서는 별도 소유자 검증을 하지 않는다.
2. **직접 호출:** `get_db()` → **bids.update_one({_id: bid_id}, {$set: document}, upsert=True)** → **orders.find_one({_id: bid_id}, {_id:0})**.
3. **반환·상태:** 입찰 쓰기는 bids에 반영되지만 반환은 orders 조회 결과다. 보통 None이며 우연히 같은 ID의 orders 문서가 있으면 그 문서다. JSON bids view는 None을 안전한 dict로 바꾸지 않고 JsonResponse에 넘기므로 TypeError/500으로 이어질 수 있다. 웹 bid_view는 반환값을 사용하지 않고 bids 목록을 다시 읽는다.

## `def list_bid_documents(owner_user_id)`

Signature: `def list_bid_documents(owner_user_id)` · 소스 81행.

1. **검증·변환:** owner_user_id를 목록 조회 조건으로 사용한다.
2. **직접 호출:** `get_db().bids.find({owner_user_id: ...}, {_id:0}).sort("campaign_id", 1)` → list.
3. **반환·상태:** 해당 소유자의 입찰을 캠페인 ID 오름차순 목록으로 반환한다.

## 현재 구현에서 확인할 점

현재 save_bid_document는 **bids에 저장하고 orders에서 읽어 반환**한다. 문서는 실제 구현을 기록하며 교안의 수정본을 적용했다고 가정하지 않는다.
