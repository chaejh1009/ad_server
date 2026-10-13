# 광고 서버 (ad_server)

`game_server`와 연동하는 Django 기반 광고 서버입니다. 광고주는 캠페인·입찰과 게시된 일별 보고서를 확인하고, 게임 서버는 매체 인증을 거쳐 광고 선택 API를 호출합니다. 게임 ORM에 직접 접근하지 않고 매체가 전달한 공개 식별자와 문맥을 사용합니다.

## 구성

| 항목 | 역할 |
| --- | --- |
| Django 5.2 | 광고주 웹 화면, 세션 인증, JSON API |
| SQLite | Django 사용자·세션·관리자 데이터 |
| MongoDB / PyMongo | 캠페인, 입찰, 광고 선택 이력, 노출·클릭 사건, 게시된 보고서 |
| python-dotenv | 프로젝트 루트의 `.env` 로딩 |

```text
ad_server/
├── ad_config/
│   ├── manage.py
│   └── ad_config/        # Django 설정과 최상위 URL
├── ads/
│   ├── services.py       # 검증과 광고 선택 정책
│   ├── events.py         # 선택 스냅샷 기반 노출·클릭 기록
│   ├── exporting.py      # 사건 NDJSON 입출력·내보내기
│   ├── snapshot_intake.py # 공개 스냅샷 검사·비교·누락 기록·계약·폴더 인계
│   ├── context_projection.py # 수신 계약 대조·공개 subject/context 정규화
│   ├── timestamps.py     # ISO 시각 UTC 정규화
│   ├── delivery.py       # 미전달 사건의 로컬 파일 전달·표식 갱신
│   ├── reporting.py      # 서울 노출일별 집계·보고서 게시·조회
│   ├── management/commands/ # 사건·보고서·스냅샷 명령과 정규화 미리보기·CDC 준비 기록
│   ├── repository.py     # 캠페인·입찰 저장 및 조회
│   ├── mongo.py          # MongoDB 연결 풀
│   ├── media_auth.py     # 매체 서버 인증
│   ├── templates/        # 로그인·캠페인·입찰·실적·일별 보고서 화면
│   └── statics/          # 광고 이미지
├── docs/ad-server-routing/ # HTTP·관리 명령·파일별 호출 문서
├── config/mongo-node1.yml
├── example.env
└── requirements.txt
```

## 로컬 실행

Python 3.12 기준이며, MongoDB 서버(`mongod`)와 MongoDB Shell(`mongosh`)이 설치되어 있어야 합니다. 아래 명령은 저장소 루트에서 실행합니다.

### 1. 가상환경과 환경변수

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp example.env .env
```

`.env`의 예시 키를 변경합니다.

| 변수 | 설명 |
| --- | --- |
| `MONGO_URI` | MongoDB 접속 URI. 로컬 예시: `mongodb://localhost:27017/?replicaSet=ads-rs` |
| `MONGO_DB` | 광고 DB 이름. 기본값 `village_ads` |
| `ADS_SECRET_KEY` | Django 비밀키 설정용 변수. 현재 코드의 덮어쓰기 문제는 아래 참고 |
| `ADS_BASE_URL` | 광고 서버 주소. 기본값 `http://127.0.0.1:8001` |
| `ADS_MEDIA_ID` | 인증할 매체 ID. 현재 지원 매체는 `village-game` |
| `ADS_MEDIA_KEY` | 매체 서버와 공유하는 인증 키 |

`ADS_MEDIA_KEY`는 게임 서버에서 보내는 `X-Media-Key`와 같아야 합니다. `.env`, `.venv`, DB 데이터, 캐시 및 로그는 Git에서 제외하며, `example.env`는 공유합니다.

### 2. MongoDB 실행

```bash
mkdir -p infra/mongo/data/node1
mongod --config config/mongo-node1.yml
```

MongoDB를 실행한 상태에서 다른 터미널로 최초 한 번 복제 세트를 초기화합니다. 이미 초기화한 데이터 디렉터리는 다시 초기화하지 않습니다.

```bash
mongosh 'mongodb://localhost:27017/?directConnection=true' --eval 'rs.initiate({_id: "ads-rs", members: [{_id: 0, host: "localhost:27017"}]})'
```

설정 파일은 `localhost:27017`에 단일 노드를 실행하며, 복제 세트 이름은 `ads-rs`입니다.

### 3. Django 실행

가상환경을 활성화한 터미널에서 실행합니다.

```bash
python ad_config/manage.py migrate
python ad_config/manage.py createsuperuser
python ad_config/manage.py runserver 127.0.0.1:8001
```

`migrate`는 SQLite에 Django 인증·세션 테이블을 만듭니다. 광고 데이터는 MongoDB의 `campaigns`, `bids`, `decisions`, `ad_events` 컬렉션에 저장됩니다. `load_ad_reports`로 보고서를 게시하면 `ad_daily_reports`도 사용합니다.

## 광고주 사용 순서

1. `http://127.0.0.1:8001/accounts/login/`에서 생성한 계정으로 로그인합니다.
2. `/advertiser/campaigns/`에서 캠페인을 등록합니다.
3. `/advertiser/bids/`에서 본인 소유의 활성 캠페인에 입찰합니다.
4. 게임 서버가 광고 선택 API를 호출하면 해당 매체·슬롯의 후보 중 광고를 선택합니다.
5. 매체가 실제 표시·클릭 뒤 사건 API를 호출하면 `/advertiser/events/`에서 본인 소유의 최근 선택 30개와 노출·클릭 시각을 확인합니다. 광고 선택만으로 노출이 기록되지는 않습니다.

6. 아래 보고서 명령으로 사건 파일을 집계·게시한 뒤 `/advertiser/reports/`에서 본인의 서울 노출일별 노출·클릭·CTR·모의 포인트 합을 확인합니다.

캠페인 ID는 2~48자의 소문자·숫자·하이픈이며 첫 글자는 소문자 또는 숫자여야 합니다. 제목은 공백을 제거한 뒤 1~80자입니다. 광고 슬롯은 `village-board`, `lobby-banner`를 지원합니다.

이미지 경로는 `/static/ads/creatives/` 아래의 PNG, JPG, JPEG, WEBP만 허용합니다. 기본 화면에서는 `forest-tools.png`와 `camp-tea.png`를 선택할 수 있습니다.

## API

### 광고주 인증 및 관리

| 메서드 | 경로 | 기능 |
| --- | --- | --- |
| GET | `/api/auth/csrf/` | CSRF 쿠키 및 `csrfToken` 발급 |
| POST | `/api/auth/login/` | `username`, `password` JSON으로 세션 로그인 |
| POST | `/api/auth/logout/` | 세션 로그아웃 |
| GET / POST | `/api/ads/campaigns/` | 본인 캠페인 조회 / 저장 |
| GET / POST | `/api/ads/bids/` | 본인 입찰 조회 / 저장 |

광고주 API는 Django 세션 쿠키를 사용합니다. POST 요청에는 CSRF 토큰을 `X-CSRFToken` 헤더로 보내며 쿠키도 유지해야 합니다. 로그인 후에는 갱신된 CSRF 토큰을 사용합니다. JSON 본문은 `Content-Type: application/json`으로 전송합니다.

캠페인 저장 본문 예시:

```json
{
  "campaign_id": "forest-tools",
  "title": "숲 도구 상점",
  "creative_path": "/static/ads/creatives/forest-tools.png",
  "media_id": "village-game",
  "slot_id": "village-board",
  "active": true
}
```

입찰 저장 본문 예시:

```json
{
  "campaign_id": "forest-tools",
  "bid_units": 100
}
```

입찰은 `bool`을 제외한 1~10000의 정수입니다. 캠페인별 입찰 문서 한 건을 유지하며 재입찰하면 값을 갱신합니다. 목록 응답은 `{"rows": [...]}` 형태입니다.

### 게임 서버의 광고 선택

`POST /api/media/decision/`은 광고주 세션 대신 `X-Media-ID`, `X-Media-Key` 헤더로 인증하며 CSRF 검사를 면제합니다. 아래 예시의 키는 `.env`에 설정한 실제 공유 키로 바꿉니다.

```bash
curl -X POST http://127.0.0.1:8001/api/media/decision/ \
  -H 'Content-Type: application/json' \
  -H 'X-Media-ID: village-game' \
  -H 'X-Media-Key: replace-with-a-shared-media-key' \
  -d '{"subject":{"media_id":"village-game","subject_id":"player-1"},"slot_id":"village-board","context":{"player_id":1}}'
```

`subject.media_id`는 인증 헤더와 일치해야 하며, `subject_id`는 1~128자의 문자열입니다. `context`는 최대 16개 항목의 객체이며 값으로 문자열·숫자·불리언·null만 허용합니다. 키는 1~64자, 문자열 값은 최대 256자입니다.

선택 정책은 `highest-bid-v1`입니다. 같은 매체·슬롯의 활성 캠페인과 활성 입찰 중 소유자가 일치하는 후보를 모아 입찰액 내림차순으로 정렬합니다. 동점이면 캠페인 ID 오름차순으로 선택합니다. 현재 `context`는 선택 이력에 보존하며 타기팅 순위에는 사용하지 않습니다.

광고가 선택된 응답 예시:

```json
{
  "empty": false,
  "decision_id": "생성된 UUID",
  "campaign_id": "forest-tools",
  "title": "숲 도구 상점",
  "creative_path": "/static/ads/creatives/forest-tools.png",
  "slot_id": "village-board",
  "bid_units": 100,
  "policy_version": "highest-bid-v1"
}
```

선택 시 응답 정보, 후보별 입찰액·소유자, subject, context, 선택 시각을 `decisions`에 저장합니다. 저장 문서는 `owner_user_id`, `chosen_campaign_id`, `chosen_bid_amount`, UTC ISO 문자열 `event_time`, `creative` 및 후보별 `bid_amount` 스냅샷을 포함합니다. 사건은 현재 입찰 대신 이 스냅샷을 사용합니다. 응답에는 `Cache-Control: no-store`가 설정됩니다. 후보가 없으면 이력을 저장하지 않고 다음 응답을 반환합니다. 현재 빈 응답의 정책 필드명은 `rule_version`입니다.

```json
{"empty": true, "slot_id": "village-board", "rule_version": "highest-bid-v1"}
```

주요 오류 응답은 인증 실패 `401`, 입력 오류 `400`, 허용하지 않는 메서드 `405`, MongoDB 오류 `503`입니다. 광고주 POST의 CSRF 검증 실패는 Django에서 `403`으로 처리합니다.

### 노출·클릭 기록과 실적 화면

`POST /api/media/events/`는 광고 선택과 같은 `X-Media-ID`, `X-Media-Key` 인증을 사용하며 CSRF 검사를 면제합니다. 선택 요청과 같은 subject, 응답으로 받은 decision_id, event_type을 전송합니다.

```json
{
  "subject": {"media_id": "village-game", "subject_id": "player-1"},
  "decision_id": "광고 선택 응답의 UUID",
  "event_type": "impression"
}
```

실제 표시 후 `impression`, 실제 클릭 후 `click`을 보냅니다. 클릭에는 선행 노출이 필요합니다. 결정과 subject가 일치하고 선택 당시 후보의 소유자·금액 스냅샷이 있어야 합니다. 과거 결정에 스냅샷이 없으면 새 광고를 요청해야 합니다.

```json
{"event_id": "결정UUID:impression", "event_type": "impression", "created": true}
```

사건 ID는 `decision_id:event_type`입니다. 같은 사건을 재전송하면 `created: false`이며 기존 시각과 값을 유지합니다. 성공 응답에 `Cache-Control: no-store`가 붙습니다. 사건은 `ad_events`에 `ad-event/v1` 스키마로 저장되고 클릭의 `impression_time`은 선행 노출 시각입니다. 인증 실패는 401, 검증 실패는 400, MongoDB 오류는 503입니다.

`GET /advertiser/events/`는 광고주 세션으로 본인 소유의 최근 결정 30개와 연결된 사건을 읽습니다. 방문 자체로 사건을 만들거나 일별 집계를 수행하지 않습니다. 일별 보고서 링크 `/advertiser/reports/`는 본인 소유의 게시된 보고서를 날짜 내림차순으로 보여줍니다. 저장소 오류는 503으로 표시합니다.

## 사건 NDJSON 내보내기와 일별 보고서

저장소 루트에서 실행합니다. 경계 시각은 시간대가 있는 ISO 형식이며, 아래 예시는 한국 시각 하루의 노출에 속하는 사건을 내보냅니다.

```bash
python ad_config/manage.py export_ad_events \
  --output data/ad-events-2026-10-07.ndjson \
  --since '2026-10-07T00:00:00+09:00' \
  --until '2026-10-08T00:00:00+09:00'
```

범위는 **impression_time 기준 [since, until)**입니다. 클릭은 해당 노출 시각을 기준으로 포함하므로 클릭의 event_time이 종료 경계 이후일 수도 있습니다. 옵션을 생략하면 해당 경계를 제한하지 않습니다. 전체 사건을 읽은 뒤 필터링하고 event_time·event_id 순서로 정렬합니다.

출력은 Mongo `_id`를 제외한 공개 12필드의 UTF-8 NDJSON이며 같은 경로의 파일을 덮어씁니다. 명령은 `path`, `rows`, `sha256`, `schema_version`, `source_kind`, UTC로 정규화한 `since`·`until`을 JSON으로 표준 출력합니다. 별도 manifest 파일은 만들지 않습니다. 로컬 `data/`는 Git에서 제외됩니다.

미전달 사건을 같은 로컬 파일에 누적하려면 다음 명령을 사용합니다. `--limit`은 한 번에 읽는 사건 수이며 기본값은 100입니다. 대기 사건이 남으면 반복 실행합니다.

```bash
python ad_config/manage.py deliver_ad_events --output data/ad-events.ndjson --limit 100
```

한 writer가 파일을 관리하는 방식입니다. 기존 파일과 사건 ID별로 병합하고 동일 ID의 내용 충돌은 거절합니다. 임시 파일을 완성해 교체한 뒤 Mongo 사건에 `file_delivered_at`을 기록합니다. 파일 교체 후 표식 기록 전에 중단되면 재실행으로 표식을 보완할 수 있습니다. 이미 표식이 있는 사건은 전달 파일이 삭제되어도 다시 선택하지 않습니다.

고정 사건 파일에서 보고서 후보를 생성하고 게시·대조합니다. 아래 대조 명령은 **전체 보관 사건 파일**과 **전체 게시 보고서**를 비교하므로 날짜별 부분 파일을 사용하면 다른 날짜의 게시 행이 추가 키로 판정될 수 있습니다.

```bash
python ad_config/manage.py build_ad_reports \
  --source data/ad-events.ndjson --output data/ad-reports.ndjson
python ad_config/manage.py load_ad_reports --source data/ad-reports.ndjson
python ad_config/manage.py check_ad_reports \
  --source data/ad-events.ndjson --output data/ad-report-check.json
```

집계는 같은 ID·내용의 사건을 중복 제거하고 클릭에 대응하는 노출이 같은 입력에 있는지 검사합니다. 클릭도 서울 기준 **노출일**에 귀속합니다. 업무 키는 `(owner_user_id, campaign_id, slot_id, date)`이며 노출 수·클릭 수·CTR(`clicks/impressions`, 0~1)과 노출의 `bid_amount` 합인 `bid_units_sum`을 기록합니다. 이 합은 모의 포인트이며 실제 청구액이 아닙니다.

`build_ad_reports`는 후보 NDJSON만 생성합니다. `load_ad_reports`는 `ad-report/v1` 스키마와 업무 키의 공백 없는 JSON 배열 문자열 `_id`를 검사한 뒤 같은 키의 문서를 전체 교체하고 `published=처리행수`를 출력합니다. 입력에 없는 기존 보고서는 유지하며 행별 저장이므로 중간 실패 시 앞서 게시한 행은 남습니다.

`check_ad_reports`는 누락·추가 키와 공통 키의 `impressions`, `clicks`, `ctr`, `bid_units_sum`, `source_max_event_time`을 대조합니다. `generated_at`은 비교하지 않습니다. 원본 SHA-256·행 수·고유 사건 수·차이 목록·`ok`를 JSON 파일과 표준 출력에 기록하고, 불일치하면 증거 저장 후 실패 종료합니다. 이 명령은 게시 데이터를 수정하지 않습니다.

## 플레이어 공개 스냅샷 검사

게임 서버에서 저장한 동결 NDJSON 파일을 검사합니다. 실행 중 입력 파일을 변경하지 않으며 단일 작성자를 전제로 합니다. 파일 잠금은 제공하지 않습니다.

```bash
python ad_config/manage.py inspect_player_snapshot --source data/player-snapshot.ndjson
```

각 행은 다음 여덟 필드만 갖는 JSON 객체입니다. 계정·좌표 등 추가 필드는 거절합니다.

```json
{"id":1,"room_id":"lobby","coins":100,"version":0,"updated_at":"2026-10-08T00:00:00+00:00","schema_version":"player-snapshot/v1","source_kind":"player-snapshot","captured_at":"2026-10-08T01:00:00+00:00"}
```

`id`는 양수 정수, `room_id`는 문자열, `coins`는 정수, `version`은 0 이상 정수입니다. 정수 필드에는 불리언을 허용하지 않습니다. `updated_at`과 `captured_at`은 시간대가 있는 시각이어야 합니다. 같은 ID는 내용이 같아도 중복을 거절하며, 모든 행의 `captured_at` 원본 값이 같아야 합니다.

명령은 `rows`, 정렬된 `public_ids`, `source_kind`, `schema_version`, `captured_at`, 원본 바이트의 `sha256`을 JSON으로 표준 출력합니다. 빈 파일도 허용하며 수집 시각은 null입니다. 검증 실패는 오류로 종료합니다. 파일·DB를 수정하거나 광고 선택·보고서에 자동 반영하지 않습니다.

## CDC 준비 기록

선택 경로의 제공·존재 여부와 현재 CDC 준비 상태를 JSON으로 기록합니다. 세 경로 옵션을 생략해도 실행할 수 있습니다.

```bash
python ad_config/manage.py write_cdc_readiness --output data/cdc-readiness.json
```

`--mysql-config`, `--connect-home`, `--debezium-dir`에 경로를 지정하면 각 항목의 `supplied`와 `exists`를 기록합니다. 상대경로는 실행 작업 폴더 기준이며 파일·디렉터리 종류나 내용을 검사하지 않습니다. 출력 부모 폴더를 생성하고 UTF-8 JSON 파일을 덮어쓰며 같은 결과를 표준 출력합니다.

결과의 `schema_version`은 `cdc-readiness/v1`, `common_input`은 `player-snapshot/v1`입니다. 경로가 존재해도 `mysql_binlog`는 `not-verified`, `cdc_reader`, `connect_worker`, `debezium_connector`, `player_change_topic`은 `not-configured`, `binlog_cdc_observed`는 `false`로 유지됩니다. 실제 MySQL·Connect·Debezium 연결이나 binlog 관찰은 실행하지 않습니다. [명령 상세](docs/ad-server-routing/files/ads/management/commands/write_cdc_readiness.py.md)에서 호출·출력·오류 계약을 확인할 수 있습니다.

## 스냅샷 비교·계약·인계·미리보기

스냅샷 비교·누락 기록·계약·교육용 변경 fixture는 아래 명령으로 생성합니다. 각 결과의 의미와 출력 경로 조건은 [전체 라우팅](docs/ad-server-routing/README.md)의 관리 명령 계약을 따릅니다.

```bash
python ad_config/manage.py compare_player_snapshots --before data/before.ndjson --after data/after.ndjson --output data/player-compare.json
python ad_config/manage.py read_snapshot_missing --before data/before.ndjson --after data/after.ndjson --output data/player-missing.json
python ad_config/manage.py write_snapshot_contract --source data/player-snapshot.ndjson --output data/player-contract.json
python ad_config/manage.py write_player_change_fixture --output data/player-change-fixture.ndjson --summary data/player-change-summary.json
```

비교 결과는 `changed`, `newly_seen`, `missing_unknown`입니다. `changed`는 같은 ID의 `room_id`, `coins`, `version`, UTC로 정규화한 `updated_at`을 비교합니다. 누락 기록의 `unknown`은 이전 파일에만 있는 정렬된 ID이며 `delete_events=[]`, `delete_inference_allowed=false`로 기록합니다. 파일에서 사라졌다는 이유로 삭제 사건을 만들지 않습니다. 교육 fixture는 `teaching-fixture` 출처의 고정 `r/u/d` 세 행입니다.

원본과 계약을 새 폴더로 인계하고 첫 행의 정규화 결과를 확인합니다. `write_snapshot_contract`는 현재 소비 함수와 같은 `artifact_id="data/exports/player-cdc.ndjson"`와 `public_fields`를 생성하므로 생성한 계약을 그대로 인계할 수 있습니다. 아래 `game-player-contract.json`은 이 명령으로 원본에 맞춰 생성한 계약입니다.

```bash
python ad_config/manage.py handoff_player_snapshot --source data/player-snapshot.ndjson --contract data/game-player-contract.json --target data/received/player-v2
python ad_config/manage.py preview_player_snapshot --source data/received/player-v2/player-cdc.ndjson --contract data/received/player-v2/player-cdc-contract.json
```

인계 명령은 대상이 존재하면 거절합니다. 임시 수신 폴더에 `player-cdc.ndjson`과 `player-cdc-contract.json`을 준비하고 복사본 SHA-256을 확인한 뒤 최종 폴더로 옮깁니다. 계약의 `source_path`는 최종 수신 파일 경로로 바뀝니다. 미리보기는 전체 원본과 계약·경로·체크섬을 대조하고 첫 행만 `player-context-change/v1`의 `upsert`로 정규화하여 표준 출력합니다. `subject_id`와 `context.player_id`는 문자열이며 `change_id`는 정렬된 공개 데이터 JSON의 SHA-256입니다. `--media-id`의 기본값은 `settings.ADS_MEDIA_ID`입니다. 미리보기 결과를 광고 선택·Mongo에 저장하는 호출은 없습니다.

## 공개 context 파일과 최신 상태

수신 계약에 맞는 전체 스냅샷을 정규화 파일로 저장하고, 파일의 지정한 한 행을 Mongo `player_context`에 반영합니다. 반영 전에 파일 전체를 검증합니다.

```bash
python ad_config/manage.py normalize_player_snapshot --source data/received/player-v2/player-cdc.ndjson --contract data/received/player-v2/player-cdc-contract.json --output data/player-context.ndjson
python ad_config/manage.py inspect_player_context --source data/player-context.ndjson --subject 1
python ad_config/manage.py apply_player_context --source data/player-context.ndjson --row 1
```

검사 명령은 `(media_id, subject_id)` 고유 인덱스를 생성합니다. 반영 명령은 더 큰 version을 저장하고 같은 상태의 반복은 `duplicate`, 낮은 version은 `stale`로 처리합니다. 같은 version의 다른 상태는 오류입니다. `demo_context_versions --subject fixture-new-demo`는 새 학습 대상에 실제 저장을 수행하고 최종 삭제 표시 문서를 남깁니다. 저장 context를 광고 선택에 자동 주입하는 호출은 없습니다. [전체 호출·계약](docs/ad-server-routing/files/ads/context_projection.py.md)을 확인합니다.

## 일괄 반영·갱신과 context 조회

정규화 파일을 체크포인트와 함께 순서대로 반영합니다. `next_line`은 0-based 다음 처리 위치이며 입력 SHA가 달라지면 기존 체크포인트를 거절합니다. 현재 코드에서는 비어 있지 않은 입력에 `--checkpoint`를 생략하면 처리 위치가 전진하지 않아 종료되지 않으므로 아래처럼 지정합니다.

```bash
python ad_config/manage.py project_player_context --source data/player-context.ndjson --checkpoint data/context-checkpoint.json --limit 100
python ad_config/manage.py refresh_player_context --source data/player-snapshot.ndjson --contract data/player-contract.json
python ad_config/manage.py inspect_decision_context --subject 1 --latest
```

첫 명령을 반복하면 같은 파일의 다음 위치에서 재개합니다. 각 Mongo 반영 성공 후 체크포인트를 교체하며 두 저장은 별도 단계입니다. 갱신 명령은 새 스냅샷 전체를 버전 정책으로 반영하지만 누락 ID를 삭제하지 않습니다. 두 명령 모두 중간 오류 이전에 반영한 행은 남습니다. 비교 명령은 최신 선택 당시 context와 현재 공개 복사본의 차이를 읽기만 하며 `--decision-id ID`로 특정 결정을 지정할 수도 있습니다.

`POST /api/media/context/`는 `X-Media-ID`·`X-Media-Key`와 JSON subject를 받아 현재 context를 반환합니다. 요청 예제는 [examples/context-request.json](examples/context-request.json)이며 결과는 `{"subject": {...}, "context": {...}}`입니다. 미저장·삭제 대상의 context는 `{}`이며 성공 응답에 `Cache-Control: no-store`가 설정됩니다. 인증 실패는 401, 입력 오류는 400, Mongo 오류는 503입니다. 광고 선택은 계속 요청에 포함된 context를 스냅샷으로 저장하며 이 조회를 자동 호출하지 않습니다.

## 라우팅 문서

[문서 안내](docs/README.md)와 [전체 라우팅](docs/ad-server-routing/README.md)에서 HTTP·관리 명령 경로, 계층별 호출 흐름, Mongo·파일 계약과 파일별 함수 시그니처를 확인할 수 있습니다. 현재 문서 범위는 런타임 Python 45파일, top-level 함수·클래스 88개, 직접 정의한 클래스 메서드 41개입니다.

## 확인 및 현재 코드의 제한

```bash
python ad_config/manage.py check
python ad_config/manage.py help export_ad_events
python ad_config/manage.py help deliver_ad_events
python ad_config/manage.py help build_ad_reports
python ad_config/manage.py help load_ad_reports
python ad_config/manage.py help check_ad_reports
python ad_config/manage.py help inspect_player_snapshot
python ad_config/manage.py help compare_player_snapshots
python ad_config/manage.py help write_snapshot_contract
python ad_config/manage.py help write_player_change_fixture
python ad_config/manage.py help write_cdc_readiness
python ad_config/manage.py help read_snapshot_missing
python ad_config/manage.py help handoff_player_snapshot
python ad_config/manage.py help preview_player_snapshot
python ad_config/manage.py help normalize_player_snapshot
python ad_config/manage.py help apply_player_context
python ad_config/manage.py help inspect_player_context
python ad_config/manage.py help demo_context_versions
python ad_config/manage.py help project_player_context
python ad_config/manage.py help refresh_player_context
python ad_config/manage.py help inspect_decision_context
```

현재 시스템 검사에서는 `ads` URL namespace 중복 경고(`urls.W005`)가 발생합니다. `ads.urls`가 루트와 `/api/ads/`에 함께 등록되어 있기 때문입니다.

현재 소스에는 다음 확인 사항이 있습니다.

- `settings.py`에서 환경변수로 읽은 `SECRET_KEY`를 뒤쪽의 개발용 고정 키가 덮어씁니다. `DEBUG=True`이며 `ALLOWED_HOSTS`도 뒤에서 빈 목록으로 재설정됩니다. 운영 배포 전 설정 정리가 필요합니다.
- `repository.save_bid_document()`는 `bids`에 저장한 뒤 `orders` 컬렉션을 조회합니다. 따라서 입찰은 저장되어도 반환값이 `None`이 될 수 있으며, JSON 입찰 POST의 정상 응답 처리에 문제가 있습니다. 웹 입찰 화면은 저장 후 `bids` 목록을 다시 조회합니다.
- 자동 테스트 파일은 기본 골격 상태입니다. 시스템 검사만으로 MongoDB 저장·조회나 게임 서버 연동이 검증되지는 않습니다.
- 현재 범위는 캠페인·입찰 관리, 광고 선택 스냅샷, 노출·클릭 기록·조회, NDJSON 내보내기·전달, 일별 집계·게시·대조와 보고서 화면, 플레이어 공개 스냅샷 검사·비교·누락 기록·계약 생성·폴더 인계·정규화 미리보기·교육 fixture·CDC 준비 기록과 전체 context 정규화 파일 생성·최신 상태 반영/조회·버전 데모·체크포인트 일괄 반영·스냅샷 갱신·선택 context 비교입니다. 과금·예산 차감은 구현되어 있지 않습니다.
- 2026-10-12 문서 갱신에서 시스템 검사는 기존 namespace 경고 1건과 함께 성공했고 관리 명령 13개의 help가 정상 로딩되었습니다. 런타임 37파일·94개 기호의 문서 대응·시그니처·헤딩·링크를 확인했으며 변경사항 감사의 누락·인수 구조 불일치는 0건입니다. 임시 파일·CLI와 오류 분기 검사 47건에서 계약 불일치 거절·조건을 맞춘 인계와 미리보기·비교와 누락 기록·정규화 해시·출력 계약을 확인했습니다. 실제 동시 writer·MySQL/CDC·Mongo·브라우저·게임 연동 실행은 이번 문서 갱신에 포함하지 않았습니다.

직전 커밋 `6a75121` 이후 갱신에서는 런타임 45파일·129개 기호의 문서 대응·시그니처·링크와 새 관리 명령 3개의 help를 확인했습니다. 계약 생성/소비 필드를 일치시킨 변경과 현재 context API, 체크포인트 생략 시 반복 처리되는 제한을 반영했습니다. Django 검사에는 기존 `urls.W005` 경고 1건이 남으며 실제 Mongo·HTTP 연동은 실행하지 않았습니다.
