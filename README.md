# 광고 서버 (ad_server)

`game_server`와 연동하는 Django 기반 광고 서버입니다. 광고주는 캠페인과 입찰을 관리하고, 게임 서버는 매체 인증을 거쳐 광고 선택 API를 호출합니다. 게임 ORM에 직접 접근하지 않고 매체가 전달한 공개 식별자와 문맥을 사용합니다.

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
│   ├── timestamps.py     # ISO 시각 UTC 정규화
│   ├── reporting.py      # 보고서 게시·조회 서비스 (집계 함수 미구현)
│   ├── management/commands/ # 내보내기·보고서 후보 명령
│   ├── repository.py     # 캠페인·입찰 저장 및 조회
│   ├── mongo.py          # MongoDB 연결 풀
│   ├── media_auth.py     # 매체 서버 인증
│   ├── templates/        # 로그인·캠페인·입찰·실적 화면
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

`migrate`는 SQLite에 Django 인증·세션 테이블을 만듭니다. 광고 데이터는 MongoDB의 `campaigns`, `bids`, `decisions`, `ad_events` 컬렉션에 저장됩니다. 보고서 게시 서비스를 직접 호출하면 `ad_daily_reports`도 사용합니다.

## 광고주 사용 순서

1. `http://127.0.0.1:8001/accounts/login/`에서 생성한 계정으로 로그인합니다.
2. `/advertiser/campaigns/`에서 캠페인을 등록합니다.
3. `/advertiser/bids/`에서 본인 소유의 활성 캠페인에 입찰합니다.
4. 게임 서버가 광고 선택 API를 호출하면 해당 매체·슬롯의 후보 중 광고를 선택합니다.
5. 매체가 실제 표시·클릭 뒤 사건 API를 호출하면 `/advertiser/events/`에서 본인 소유의 최근 선택 30개와 노출·클릭 시각을 확인합니다. 광고 선택만으로 노출이 기록되지는 않습니다.

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

`GET /advertiser/events/`는 광고주 세션으로 본인 소유의 최근 결정 30개와 연결된 사건을 읽습니다. 방문 자체로 사건을 만들거나 일별 집계를 수행하지 않습니다. 현재 화면의 일별 보고서 링크 `/advertiser/reports/`에는 대응하는 URL/view가 없어 404입니다.

## 사건 NDJSON 내보내기와 보고서 구현 범위

저장소 루트에서 실행합니다. 경계 시각은 시간대가 있는 ISO 형식이며, 아래 예시는 한국 시각 하루의 노출에 속하는 사건을 내보냅니다.

```bash
python ad_config/manage.py export_ad_events \
  --output data/ad-events-2026-10-07.ndjson \
  --since '2026-10-07T00:00:00+09:00' \
  --until '2026-10-08T00:00:00+09:00'
```

범위는 **impression_time 기준 [since, until)**입니다. 클릭은 해당 노출 시각을 기준으로 포함하므로 클릭의 event_time이 종료 경계 이후일 수도 있습니다. 옵션을 생략하면 해당 경계를 제한하지 않습니다. 전체 사건을 읽은 뒤 필터링하고 event_time·event_id 순서로 정렬합니다.

출력은 Mongo `_id`를 제외한 공개 12필드의 UTF-8 NDJSON이며 같은 경로의 파일을 덮어씁니다. 명령은 `path`, `rows`, `sha256`, `schema_version`, `source_kind`, UTC로 정규화한 `since`·`until`을 JSON으로 표준 출력합니다. 별도 manifest 파일은 만들지 않습니다. 로컬 `data/`는 Git에서 제외됩니다.

`reporting.publish_reports(rows)`와 `list_reports(owner_user_id)`는 `ad-report/v1` 보고서의 Mongo 게시·조회 서비스입니다. 게시 업무 키는 `(owner_user_id, campaign_id, slot_id, date)`의 공백 없는 JSON 배열 문자열이며 같은 `_id`는 전체 교체합니다. 현재 HTTP 경로와 게시 명령은 연결되어 있지 않습니다.

`build_ad_reports --source … --output …` 관리 명령 파일은 있지만 참조하는 `reporting.build_daily_reports`가 없어 import 단계에서 실패합니다. 일별 보고서 계산과 조회 화면은 아직 사용할 수 없습니다.

## 라우팅 문서

[문서 안내](docs/README.md)와 [전체 라우팅](docs/ad-server-routing/README.md)에서 HTTP 경로, 계층별 호출 흐름, Mongo 문서 계약과 파일별 함수 시그니처를 확인할 수 있습니다. 현재 문서 범위는 런타임 Python 23파일, top-level 함수·클래스 42개, 직접 정의한 클래스 메서드 4개입니다.

## 확인 및 현재 코드의 제한

```bash
python ad_config/manage.py check
python ad_config/manage.py help export_ad_events
```

현재 시스템 검사에서는 `ads` URL namespace 중복 경고(`urls.W005`)가 발생합니다. `ads.urls`가 루트와 `/api/ads/`에 함께 등록되어 있기 때문입니다.

현재 소스에는 다음 확인 사항이 있습니다.

- `settings.py`에서 환경변수로 읽은 `SECRET_KEY`를 뒤쪽의 개발용 고정 키가 덮어씁니다. `DEBUG=True`이며 `ALLOWED_HOSTS`도 뒤에서 빈 목록으로 재설정됩니다. 운영 배포 전 설정 정리가 필요합니다.
- `repository.save_bid_document()`는 `bids`에 저장한 뒤 `orders` 컬렉션을 조회합니다. 따라서 입찰은 저장되어도 반환값이 `None`이 될 수 있으며, JSON 입찰 POST의 정상 응답 처리에 문제가 있습니다. 웹 입찰 화면은 저장 후 `bids` 목록을 다시 조회합니다.
- 자동 테스트 파일은 기본 골격 상태입니다. 시스템 검사만으로 MongoDB 저장·조회나 게임 서버 연동이 검증되지는 않습니다.
- 현재 범위는 캠페인·입찰 관리, 광고 선택 스냅샷, 노출·클릭 사건 기록·실적 조회와 NDJSON 내보내기입니다. 과금·예산 차감·일별 집계 함수·보고서 HTTP 화면은 구현되어 있지 않습니다.
- 2026-10-07 점검에서 시스템 검사는 기존 namespace 경고 1건과 함께 성공했고 내보내기 명령 help도 정상 로딩되었습니다. 보고서 후보 명령 help는 미정의 `build_daily_reports` ImportError로 실패했습니다. 실제 Mongo 저장·내보내기와 게임 연동은 이번 점검에서 실행하지 않았습니다.
