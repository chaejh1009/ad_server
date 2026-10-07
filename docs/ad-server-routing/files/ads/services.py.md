# `ads/services.py`

원본 소스 경로: `ads/services.py` · 광고 작업 폴더 기준. [전체 라우팅](../../README.md)

## 책임과 경계

공개 식별자·입력 검증, 광고주 캠페인·입찰 유스케이스, 후보 순위와 결정 스냅샷 생성을 소유한다. HTTP request·게임 ORM·이미지 다운로드를 사용하지 않는다.

## 호출자와 직접 의존

views·web_views·media_auth·events.

관련 문서: [ads/repository.py](repository.py.md), [ads/mongo.py](mongo.py.md).

## 소유한 값

`MEDIA_SLOTS={"village-game": {"village-board", "lobby-banner"}}`, `SLOTS`는 이 매체 슬롯 집합의 별칭, `MAX_BID_UNITS=10000`, `POLICY_VERSION="highest-bid-v1"`이다.

## `def clean_subject(value)`

Signature: `def clean_subject(value)` · 소스 18행.

1. **검증·변환:** dict 여부, 등록된 문자열 media_id, 길이 1~128의 문자열 subject_id를 검사한다. 숫자 ID를 문자열로 자동 변환하거나 공백을 strip하지 않는다.
2. **직접 호출:** MEDIA_SLOTS 조회와 기본 타입·길이 검사만 수행한다. DB·게임 ORM 호출은 없다.
3. **반환·상태:** media_id·subject_id 두 필드만 갖는 새 dict를 반환한다. 추가 입력 필드는 보존하지 않는다. 오류는 ValueError다.

## `def clean_context(value)`

Signature: `def clean_context(value)` · 소스 31행.

1. **검증·변환:** 최대 16항목 dict, 길이 1~64의 문자열 키, None 또는 정확한 str/int/float/bool 값, 문자열 값 최대 256자를 검사한다. 중첩 dict/list는 허용하지 않는다.
2. **직접 호출:** 입력 items 반복과 타입·길이 검사. 외부 I/O는 없다.
3. **반환·상태:** 얕게 복사한 dict를 반환하거나 ValueError를 발생시킨다. float의 유한성이나 의미상 허용 키를 별도로 검사하는 코드는 없다.

## `def utc_now()`

Signature: `def utc_now()` · 소스 44행.

1. **검증·변환:** 입력·추가 검증이 없다.
2. **직접 호출:** datetime.now(timezone.utc).
3. **반환·상태:** 시간대가 있는 현재 UTC datetime을 반환한다.

## `def clean_id(value, label)`

Signature: `def clean_id(value, label)` · 소스 49행.

1. **검증·변환:** 문자열이며 [a-z0-9][a-z0-9-]{1,47} 정규식과 일치해야 한다. 전체 길이 2~48자, 소문자·숫자·하이픈만 허용한다.
2. **직접 호출:** re.fullmatch(...).
3. **반환·상태:** 입력 문자열을 그대로 반환한다. 변환하지 않으며 실패하면 label을 포함한 ValueError를 올린다.

## `def clean_slot(value, media_id='village-game')`

Signature: `def clean_slot(value, media_id='village-game')` · 소스 58행.

1. **검증·변환:** 문자열이고 MEDIA_SLOTS.get(media_id, set())에 등록되어 있는지 검사한다. 기본 매체는 village-game이다.
2. **직접 호출:** MEDIA_SLOTS의 매체별 슬롯 조회. DB 호출은 없다.
3. **반환·상태:** 그대로의 slot_id 또는 ValueError("unknown slot_id").

## `def clean_creative(value)`

Signature: `def clean_creative(value)` · 소스 66행.

1. **검증·변환:** 문자열·/static/ads/creatives/ 접두어를 검사한다. PurePosixPath.parts의 .., 역슬래시, query, fragment를 거절한다. suffix를 소문자로 비교해 png/jpg/jpeg/webp만 허용한다.
2. **직접 호출:** PurePosixPath(value)와 문자열·suffix 검사. 파일 존재 확인·다운로드는 하지 않는다.
3. **반환·상태:** 입력 경로를 그대로 반환하거나 ValueError다. percent encoding이나 반복 slash·단일 점 segment를 별도로 검사하는 구현은 없다.

## `def save_campaign(user, data)`

Signature: `def save_campaign(user, data)` · 소스 80행.

1. **검증·변환:** campaign_id를 clean_id로 검사한다. strip한 제목은 1~80자, active는 기본 True이며 정확한 bool이어야 한다. 이미지 경로와 매체별 슬롯을 검사한다.
2. **직접 호출:** clean_id → utc_now → clean_creative·clean_slot → save_campaign_document(document).
3. **반환·상태:** 소유자를 user.pk로 고정한 schema_version=1 문서를 저장하고 repository 반환값을 반환한다. 생성/갱신 시각은 UTC datetime이다.

## `def list_campaigns(user)`

Signature: `def list_campaigns(user)` · 소스 107행.

1. **검증·변환:** 입력 user의 pk로 범위를 정한다. HTTP 인증은 view의 책임이다.
2. **직접 호출:** list_campaign_documents(user.pk).
3. **반환·상태:** repository가 반환한 본인 캠페인 목록을 그대로 반환한다.

## `def save_bid(user, data)`

Signature: `def save_bid(user, data)` · 소스 112행.

1. **검증·변환:** campaign_id와 bool을 제외한 정수 1~10000 bid_units를 검사한다. campaigns에서 _id·user.pk 소유·active=True인 캠페인이 있어야 한다.
2. **직접 호출:** clean_id → get_db().campaigns.find_one(...) → utc_now → save_bid_document(document).
3. **반환·상태:** bid_id=campaign_id, 슬롯·매체는 캠페인에서 복사하고 active=True로 저장한다. repository 반환값을 그대로 넘기므로 현재 orders 반환 결함도 전파된다.

## `def list_bids(user)`

Signature: `def list_bids(user)` · 소스 141행.

1. **검증·변환:** 입력 user.pk로 소유 범위를 정한다.
2. **직접 호출:** list_bid_documents(user.pk).
3. **반환·상태:** 본인의 입찰 목록을 반환한다.

## `def candidate_rows(slot_id, media_id='village-game')`

Signature: `def candidate_rows(slot_id, media_id='village-game')` · 소스 145행.

1. **검증·변환:** 같은 media_id·slot_id·active=True 캠페인/입찰을 읽는다. 캠페인이 없거나 소유자가 다르거나 금액이 bool/비정수/범위 밖이면 해당 후보를 건너뛴다.
2. **직접 호출:** get_db() → campaigns.find(...)로 campaign_id 사전 구성 → bids.find(...) → sorted(rows, key=(-bid_units, campaign_id)).
3. **반환·상태:** campaign_id·owner_user_id·title·creative_path·slot_id·bid_units 후보 목록을 반환한다. 금액 내림차순, 동점은 캠페인 ID 오름차순이다. 직접 저장하지 않는다.

## `def choose_ad(subject, slot_id, context)`

Signature: `def choose_ad(subject, slot_id, context)` · 소스 176행.

1. **검증·변환:** clean_subject → clean_slot(slot_id, subject.media_id) → clean_context를 거친 뒤 같은 매체·슬롯 후보를 구한다.
2. **직접 호출:** candidate_rows → 후보 첫 항목 선택 → str(uuid4())·utc_now → get_db().decisions.insert_one(...).
3. **반환·상태:** 후보가 없으면 {empty:True, slot_id, rule_version}만 반환하고 결정을 저장하지 않는다. 선택되면 empty=False·decision_id·campaign_id·title·creative_path·slot_id·bid_units·policy_version을 반환한다. decisions에는 이 응답과 subject/context·소유자·selected_at·event_time·chosen_campaign_id/chosen_bid_amount·creative·후보별 owner_user_id/bid_amount 호환 스냅샷을 새 문서로 저장한다. 선택 자체는 노출/클릭을 만들지 않는다.

## 결정 스냅샷과 사건 저장의 연결

`choose_ad`는 선택 성공 시에만 아래 필드를 decisions에 추가한다. 반환 JSON에는 이 저장 전용 필드가 추가되지 않는다.

| 필드 | 값·후속 소비자 |
|---|---|
| `owner_user_id` | 선택 후보의 소유자. `web_views.event_view`의 본인 결정 조회 조건 |
| `chosen_campaign_id`, `chosen_bid_amount` | 선택 후보의 campaign_id·bid_units. 실적 화면 표시값이며 사건은 chosen_campaign_id로 후보를 찾는다. |
| `event_time` | `selected_at.isoformat()`의 UTC 문자열 |
| `creative` | `{title: 선택 후보 제목, body: ""}` |
| `candidates` | 각 후보의 campaign_id·bid_units·owner_user_id·bid_amount. bid_amount는 bid_units와 같은 값이다. |

`events.record_ad_event`는 candidates의 선택 후보에서 소유자·금액을 복사한다. 최상위 chosen_bid_amount로 누락된 후보 정보를 보충하지 않는다. 자세한 검증과 저장 계약은 [ads/events.py](events.py.md)를 따른다.

## 현재 구현에서 확인할 점

현재 choose_ad의 빈 응답은 rule_version, 선택 응답은 policy_version을 사용한다. 기존 결정은 입찰이 바뀌어도 수정하지 않는다. 사건 저장은 별도 events 함수의 책임이다.
