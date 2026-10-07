# `ads/events.py`

원본 소스 경로: `ads/events.py` · 광고 작업 폴더 기준. [전체 라우팅](../../README.md)

## 책임과 경계

선택 당시 결정 스냅샷과 매체 subject를 확인해 노출·클릭 사건을 한 종류당 한 번 저장한다. 게임 Player나 현재 입찰을 조회하지 않는다.

## 호출자와 직접 의존

매체 사건 view `ads.views.event`.

관련 문서: [ads/services.py](services.py.md), [ads/mongo.py](mongo.py.md), [ads/views.py](views.py.md).

## `def record_ad_event(subject, decision_id, event_type)`

Signature: `def record_ad_event(subject, decision_id, event_type)` · 소스 8행.

1. **검증·변환:** clean_subject로 식별자를 정규화한다. 비어 있지 않은 문자열 decision_id, impression/click 종류를 검사한다. 결정은 _id와 subject.media_id·subject.subject_id의 점 표기 조건으로 읽는다. chosen_campaign_id·candidates 목록·선택 후보의 int 소유자/양수 int 금액·문자열 slot_id를 확인한다. click에는 선행 impression이 필요하다.
2. **직접 호출:** `clean_subject()` → `get_db()` → decisions.find_one → 선택 후보 next → ad_events.find_one(impression) → datetime.now(timezone.utc) → ad_events.update_one({_id:event_id}, {$setOnInsert:document}, upsert=True).
3. **반환·상태:** ad-event/v1 문서를 최초 한 번 삽입한다. click의 impression_time은 선행 노출 event_time을 복사한다. 당시 owner_user_id·bid_amount는 후보에서 복사한다. 반환은 event_id·event_type·created(bool). 재전송은 created=False이며 기존 시각·값을 덮어쓰지 않는다. DuplicateKeyError도 False로 처리한다. 수신자 불일치 decision_not_found_for_subject, 과거 스냅샷 누락 decision_snapshot_missing, 클릭 선행 노출 없음 impression_required 등을 ValueError로 올린다.

## 저장 문서 계약

`ad_events`에는 다음 값을 `$setOnInsert`로 저장한다. 소유자와 금액은 요청 본문이나 현재 입찰이 아니라 결정의 선택 후보에서 가져온다.

| 필드 | 값·출처 |
|---|---|
| `_id`, `event_id` | `decision_id + ":" + event_type` |
| `schema_version` | 문자열 `ad-event/v1` |
| `decision_id`, `event_type` | 검증한 요청 값 |
| `event_time` | 서버 수신 처리 시점의 UTC ISO 문자열 |
| `impression_time` | impression은 자신의 event_time, click은 선행 impression의 event_time |
| `media_id`, `subject` | `clean_subject`가 반환한 인증 대상 식별자 |
| `slot_id`, `campaign_id` | 결정의 slot_id·chosen_campaign_id |
| `owner_user_id`, `bid_amount` | candidates에서 chosen_campaign_id와 일치하는 첫 후보의 값 |

## 검증 실패와 재전송

| 조건 | 발생하는 ValueError 메시지 |
|---|---|
| decision_id가 문자열이 아니거나 빈 문자열 | `decision_id_required` |
| event_type이 impression/click 이외의 값 | `event_type_invalid` |
| decision_id와 subject의 두 식별자가 일치하는 결정 없음 | `decision_not_found_for_subject` |
| chosen_campaign_id·후보 목록·선택 후보의 소유자/금액·슬롯 검증 실패 | `decision_snapshot_missing: 광고를 새로 요청하세요.` |
| click 요청에 선행 impression 없음 | `impression_required` |

subject 검증 오류는 `clean_subject`에서 전달된다. 위 검증을 모두 통과한 뒤 저장하며, 재전송도 같은 검증을 다시 거친다. 소유자·금액은 정확한 int여야 하므로 bool은 거절한다. 금액은 1 이상인지 검사하며 여기서는 `MAX_BID_UNITS` 상한을 재검사하지 않는다. slot_id는 문자열 여부만 확인한다.

## 현재 구현에서 확인할 점

사건 ID는 `decision_id:event_type`이며 Mongo 기본 _id 고유성이 적용된다. 이 함수는 복합 색인을 생성하거나 통계·파일 전송을 실행하지 않는다.
