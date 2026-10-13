# Ad server routing

이 문서는 `python ad_config/manage.py runserver 127.0.0.1:8001`로 실행하는 현재 광고 서버의 탐색 진입점이다. 광고주 세션·매체 서버 인증·Mongo 저장의 호출 경계를 기록한다. 소스의 AST·Git 변경사항을 대조했으며, Django 시스템 검사와 관리 명령 로딩 결과를 함께 기록했다. 비밀값은 문서에 복제하지 않는다.

## 범위

직접 유지보수하는 런타임 Python 전체가 대상이다. 프로젝트 루트 상대경로를 유지하여 `files/<프로젝트 상대경로>.md`와 정확히 하나씩 대응시켰다. 현재 대상은 **45파일·88개 top-level 함수/클래스 기호·41개 직접 정의한 클래스 메서드**다. signature는 `python-routing-diff-audit/scripts/audit_routing.py`의 `inventory()` 출력과 일치한다.

| 실제 파일 | 라우팅 문서 | 책임 |
|---|---|---|
| `ad_config/ad_config/asgi.py` | [`files/ad_config/ad_config/asgi.py.md`](files/ad_config/ad_config/asgi.py.md) | ASGI 서버가 import할 Django `application` 객체를 만든다. |
| `ad_config/ad_config/settings.py` | [`files/ad_config/ad_config/settings.py.md`](files/ad_config/ad_config/settings.py.md) | 광고 서버의 경로·환경설정·Django 앱/미들웨어·SQLite 인증 저장소·Mongo 연결 값·정적 파일 검색 위치를 정의한다. |
| `ad_config/ad_config/urls.py` | [`files/ad_config/ad_config/urls.py.md`](files/ad_config/ad_config/urls.py.md) | 광고 서버의 최상위 URL 접두어와 Django 인증·admin view를 연결한다. |
| `ad_config/ad_config/wsgi.py` | [`files/ad_config/ad_config/wsgi.py.md`](files/ad_config/ad_config/wsgi.py.md) | WSGI 서버가 import할 Django `application` 객체를 만든다. |
| `ad_config/manage.py` | [`files/ad_config/manage.py.md`](files/ad_config/manage.py.md) | Django 관리 명령의 프로세스 진입점이다. |
| `ads/admin.py` | [`files/ads/admin.py.md`](files/ads/admin.py.md) | Django admin 등록을 위한 앱 모듈이다. |
| `ads/apps.py` | [`files/ads/apps.py.md`](files/ads/apps.py.md) | Django가 광고 앱을 로드할 때 사용하는 앱 메타데이터를 선언한다. |
| `ads/auth_views.py` | [`files/ads/auth_views.py.md`](files/ads/auth_views.py.md) | JSON 클라이언트용 CSRF 토큰·로그인·로그아웃을 제공한다. |
| `ads/events.py` | [`files/ads/events.py.md`](files/ads/events.py.md) | 선택 당시 결정 스냅샷과 매체 subject를 확인해 노출·클릭 사건을 한 종류당 한 번 저장한다. |
| `ads/media_auth.py` | [`files/ads/media_auth.py.md`](files/ads/media_auth.py.md) | 게임 등 매체 서버의 POST를 두 헤더와 공개 subject로 인증하는 decorator factory다. |
| `ads/media_urls.py` | [`files/ads/media_urls.py.md`](files/ads/media_urls.py.md) | 최상위 `api/media/` 뒤에 붙는 매체 전용 선택·사건·현재 context 조회 경로를 등록한다. |
| `ads/models.py` | [`files/ads/models.py.md`](files/ads/models.py.md) | 광고 앱의 Django ORM 모델 정의 위치다. |
| `ads/mongo.py` | [`files/ads/mongo.py.md`](files/ads/mongo.py.md) | 한 프로세스의 MongoClient 연결 풀과 설정된 광고 Database 핸들을 제공한다. |
| `ads/repository.py` | [`files/ads/repository.py.md`](files/ads/repository.py.md) | 캠페인·입찰 문서의 PyMongo 저장·목록 조회를 담당한다. |
| `ads/services.py` | [`files/ads/services.py.md`](files/ads/services.py.md) | 공개 식별자·입력 검증, 광고주 캠페인·입찰 유스케이스, 후보 순위와 결정 스냅샷 생성을 소유한다. |
| `ads/urls.py` | [`files/ads/urls.py.md`](files/ads/urls.py.md) | 광고주 HTML 화면과 세션 JSON 관리 API의 앱 상대 경로를 등록한다. |
| `ads/views.py` | [`files/ads/views.py.md`](files/ads/views.py.md) | 광고주 세션 JSON API와 매체 서버 JSON API를 서비스 함수에 연결한다. |
| `ads/web_views.py` | [`files/ads/web_views.py.md`](files/ads/web_views.py.md) | 광고주 세션으로 캠페인·입찰을 편집하고 자신의 최근 결정·사건·게시된 일별 보고서를 HTML로 읽는다. |
| `ads/exporting.py` | [`files/ads/exporting.py.md`](files/ads/exporting.py.md) | 사건 NDJSON 내보내기·읽기·쓰기와 SHA-256 계산 |
| `ads/reporting.py` | [`files/ads/reporting.py.md`](files/ads/reporting.py.md) | 서울 노출일별 사건 집계·보고서 업무 키 검증·Mongo 게시·소유자별 조회 |
| `ads/timestamps.py` | [`files/ads/timestamps.py.md`](files/ads/timestamps.py.md) | 시간대가 있는 ISO 시각의 UTC 정규화 |
| `ads/management/commands/export_ad_events.py` | [`files/ads/management/commands/export_ad_events.py.md`](files/ads/management/commands/export_ad_events.py.md) | 사건 내보내기 CLI 옵션과 메타데이터 출력 |
| `ads/management/commands/build_ad_reports.py` | [`files/ads/management/commands/build_ad_reports.py.md`](files/ads/management/commands/build_ad_reports.py.md) | 고정 사건 파일에서 일별 보고서 후보 생성 CLI |
| `ads/delivery.py` | [`files/ads/delivery.py.md`](files/ads/delivery.py.md) | 미전달 사건의 로컬 NDJSON 교체·Mongo 전달 표식 갱신 |
| `ads/management/commands/deliver_ad_events.py` | [`files/ads/management/commands/deliver_ad_events.py.md`](files/ads/management/commands/deliver_ad_events.py.md) | 로컬 사건 전달 CLI |
| `ads/management/commands/load_ad_reports.py` | [`files/ads/management/commands/load_ad_reports.py.md`](files/ads/management/commands/load_ad_reports.py.md) | 후보 보고서의 업무 키별 Mongo 게시 CLI |
| `ads/management/commands/check_ad_reports.py` | [`files/ads/management/commands/check_ad_reports.py.md`](files/ads/management/commands/check_ad_reports.py.md) | 전체 고정 사건과 게시 보고서 대조·JSON 증거 저장 CLI |
| `ads/snapshot_intake.py` | [`files/ads/snapshot_intake.py.md`](files/ads/snapshot_intake.py.md) | 동결 플레이어 공개 스냅샷 검사·계약 생성·폴더 인계·상태 비교·누락 기록·교육 fixture 해석과 CDC 준비 상태 생성 |
| `ads/context_projection.py` | [`files/ads/context_projection.py.md`](files/ads/context_projection.py.md) | 원본·수신 계약 대조·전체 정규화 파일 저장·공개 context 버전별 Mongo 반영/조회 |
| `ads/management/commands/inspect_player_snapshot.py` | [`files/ads/management/commands/inspect_player_snapshot.py.md`](files/ads/management/commands/inspect_player_snapshot.py.md) | 플레이어 스냅샷 검사·JSON 요약 CLI |
| `ads/management/commands/write_cdc_readiness.py` | [`files/ads/management/commands/write_cdc_readiness.py.md`](files/ads/management/commands/write_cdc_readiness.py.md) | 선택 경로의 제공·존재 여부와 CDC 준비 상태를 JSON 파일·표준 출력으로 기록하는 CLI |
| `ads/management/commands/compare_player_snapshots.py` | [`files/ads/management/commands/compare_player_snapshots.py.md`](files/ads/management/commands/compare_player_snapshots.py.md) | 두 동결 스냅샷의 ID별 상태 비교·JSON 저장 CLI |
| `ads/management/commands/write_snapshot_contract.py` | [`files/ads/management/commands/write_snapshot_contract.py.md`](files/ads/management/commands/write_snapshot_contract.py.md) | 검사한 스냅샷의 인계 메타데이터·JSON 저장 CLI |
| `ads/management/commands/write_player_change_fixture.py` | [`files/ads/management/commands/write_player_change_fixture.py.md`](files/ads/management/commands/write_player_change_fixture.py.md) | 교육용 r/u/d NDJSON·해석 요약 생성 CLI |
| `ads/management/commands/read_snapshot_missing.py` | [`files/ads/management/commands/read_snapshot_missing.py.md`](files/ads/management/commands/read_snapshot_missing.py.md) | 이전 스냅샷에만 있는 ID를 삭제 추론 없이 JSON 기록하는 CLI |
| `ads/management/commands/handoff_player_snapshot.py` | [`files/ads/management/commands/handoff_player_snapshot.py.md`](files/ads/management/commands/handoff_player_snapshot.py.md) | 검사한 원본·계약을 새로운 수신 폴더로 인계하는 CLI |
| `ads/management/commands/preview_player_snapshot.py` | [`files/ads/management/commands/preview_player_snapshot.py.md`](files/ads/management/commands/preview_player_snapshot.py.md) | 원본·수신 계약을 대조한 뒤 첫 입력 행과 정규화 결과를 표준 출력하는 CLI |
| `ads/management/commands/normalize_player_snapshot.py` | [`files/ads/management/commands/normalize_player_snapshot.py.md`](files/ads/management/commands/normalize_player_snapshot.py.md) | 수신 스냅샷 전체의 정규화 NDJSON 저장 CLI |
| `ads/management/commands/apply_player_context.py` | [`files/ads/management/commands/apply_player_context.py.md`](files/ads/management/commands/apply_player_context.py.md) | 정규화 파일 전체 검증 후 지정 한 행의 Mongo 반영 CLI |
| `ads/management/commands/inspect_player_context.py` | [`files/ads/management/commands/inspect_player_context.py.md`](files/ads/management/commands/inspect_player_context.py.md) | 저장 문서 미리보기·고유 인덱스 생성·현재 context 조회 CLI |
| `ads/management/commands/demo_context_versions.py` | [`files/ads/management/commands/demo_context_versions.py.md`](files/ads/management/commands/demo_context_versions.py.md) | 새 fixture subject의 버전·반복·충돌·삭제 표시 저장 데모 CLI |
| `ads/management/inspect_player_context.py` | [`files/ads/management/inspect_player_context.py.md`](files/ads/management/inspect_player_context.py.md) | Django 자동 명령 탐색 밖의 고유 인덱스 생성·전체 context 요약 보조 모듈 |
| `ads/management/commands/project_player_context.py` | [파일 문서](files/ads/management/commands/project_player_context.py.md) | 체크포인트로 중지/재개하며 정규화 전체 파일을 Mongo 반영 CLI |
| `ads/management/commands/refresh_player_context.py` | [파일 문서](files/ads/management/commands/refresh_player_context.py.md) | 수신 스냅샷 전체의 최신 context 갱신 CLI |
| `ads/management/commands/inspect_decision_context.py` | [파일 문서](files/ads/management/commands/inspect_decision_context.py.md) | 선택 당시 context와 현재 공개 복사본 비교 CLI |

`ads/tests.py` 등 테스트, `ads/migrations/**`, 내용이 없는 `__init__.py`는 실행 호출 문서 대상에서 제외한다. `ads/admin.py`·`ads/models.py`는 현재 import/주석뿐이어도 Django 앱의 런타임 모듈이므로 포함한다. `.venv`·`__pycache__`·SQLite DB·`.env`·로그·이미지 등 생성/비밀/비Python 파일도 제외한다. 템플릿·정적 이미지의 소비 경로는 담당 view/settings 문서에 기록한다.

현재 사건 내보내기·파일 전달·일별 집계·게시·대조, 플레이어 스냅샷 검사·비교·누락 기록·계약 생성·폴더 인계·정규화 미리보기·교육 fixture·CDC 준비 기록 명령과 보고서 HTTP 조회가 연결되어 있다. 전체 정규화 파일 저장과 선택 행의 Mongo player_context 반영·조회가 추가되어 있다. 광고 선택 경로는 저장 context를 자동 조회하지 않는다. 직접 정의한 함수가 없는 설정·URL·ASGI/WSGI 모듈도 범위에서 빠지지 않는다.

## 계층별 호출 구조

```text
ad_config/manage.py main
  -> Django execute_from_command_line
     -> ad_config.settings : 경로·인증 SQLite·Mongo 값·앱·미들웨어
     -> ad_config.urls : 최상위 HTTP 경로

ASGI 서버 -> ad_config.asgi.application -> Django HTTP 처리
WSGI 서버 -> ad_config.wsgi.application -> Django HTTP 처리

ad_config.urls
  -> api/auth/* -> auth_views -> Django authenticate/login/logout/get_token
  -> accounts/login|logout -> Django 인증 form view
  -> admin/ -> Django admin
  -> "" 및 api/ads/ -> ads.urls
     -> advertiser/campaigns -> web_views.campaign_view
        -> services.save_campaign/list_campaigns
           -> repository -> mongo.get_db
     -> advertiser/bids -> web_views.bid_view
        -> services.save_bid/list_bids
           -> campaigns 조회 및 repository -> mongo.get_db
     -> advertiser/events -> web_views.event_view
        -> mongo.get_db -> decisions + ad_events 읽기
     -> advertiser/reports -> web_views.report_view
        -> reporting.list_reports -> mongo.get_db -> ad_daily_reports 읽기
     -> campaigns|bids -> views.api_methods -> views.campaigns/bids
        -> views.read_json 및 services -> repository -> mongo.get_db
  -> api/media/ -> ads.media_urls
     -> decision -> media_auth.media_api_methods -> views.decision
        -> services.choose_ad
           -> clean_subject/clean_slot/clean_context
           -> candidate_rows -> mongo.get_db -> campaigns/bids 읽기
           -> decisions.insert_one
     -> context -> media_auth.media_api_methods -> views.context_view
        -> context_projection.get_context -> player_context 읽기
     -> events -> media_auth.media_api_methods -> views.event
        -> events.record_ad_event
           -> services.clean_subject
           -> mongo.get_db -> decisions 스냅샷·선행 impression 읽기
           -> ad_events.update_one($setOnInsert)

Django 관리 명령
  -> export_ad_events.Command.handle -> exporting.export_ad_events
     -> mongo.get_db -> ad_events 읽기
     -> timestamps.parse_utc -> impression_time 범위 필터
     -> exporting.write_ndjson -> NDJSON + SHA-256
  -> deliver_ad_events.Command.handle -> delivery.deliver_events
     -> mongo.get_db -> 표식 없는 ad_events 읽기
     -> exporting.read_ndjson/write_ndjson -> 임시 파일 교체
     -> ad_events.update_one(file_delivered_at)
  -> build_ad_reports.Command.handle
     -> exporting.read_ndjson -> reporting.build_daily_reports -> exporting.write_ndjson
  -> load_ad_reports.Command.handle
     -> exporting.read_ndjson -> reporting.publish_reports -> ad_daily_reports.replace_one
  -> check_ad_reports.Command.handle
     -> exporting.read_ndjson -> reporting.build_daily_reports
     -> mongo.get_db -> ad_daily_reports 전체 읽기 -> 키·집계값 대조 -> JSON 증거 저장
  -> inspect_player_snapshot.Command.handle -> snapshot_intake.inspect_snapshot
     -> _read_snapshot -> NDJSON 바이트 읽기 + SHA-256
     -> _check_public_state + timestamps.parse_utc -> JSON 요약 표준 출력
  -> write_cdc_readiness.Command.handle -> snapshot_intake.readiness
     -> bool + Path.exists -> 선택 경로의 제공·존재 여부와 고정 CDC 상태 사전
     -> Path.parent.mkdir + Path.write_text -> JSON 파일 저장
     -> JSON 표준 출력
  -> compare_player_snapshots.Command.handle
     -> snapshot_intake.load_rows(before/after) -> inspect_snapshot + exporting.read_ndjson
     -> snapshot_intake.compare -> timestamps.parse_utc -> JSON 파일·표준 출력
  -> write_snapshot_contract.Command.handle -> snapshot_intake.build_snapshot_contract
     -> inspect_snapshot + UTC 생성 시각·고정 인계 메타데이터 -> JSON 파일·표준 출력
  -> write_player_change_fixture.Command.handle
     -> 고정 teaching-fixture r/u/d -> snapshot_intake.change_player -> _check_public_state
     -> exporting.write_ndjson -> NDJSON + SHA-256 -> 선택 요약 파일·JSON 표준 출력
  -> read_snapshot_missing.Command.handle
     -> snapshot_intake.load_rows(before/after) -> inspect_snapshot + exporting.read_ndjson
     -> snapshot_intake.missing_summary -> unknown·삭제 추론 불가 -> JSON 파일·표준 출력
  -> handoff_player_snapshot.Command.handle -> snapshot_intake.handoff_snapshot
     -> 계약 JSON 읽기 + inspect_snapshot -> 필드 대조 + timestamps.parse_utc
     -> 새 임시 수신 폴더 -> shutil.copyfile -> 원본 SHA-256 대조
     -> source_path를 수신 파일로 바꾼 계약 저장 -> 폴더 rename -> JSON 표준 출력
  -> preview_player_snapshot.Command.handle -> context_projection.read_snapshot_package
     -> 계약 JSON + inspect_snapshot -> 계약 값·source_path 대조
     -> snapshot_intake._read_snapshot -> 두 읽기 SHA-256 대조
     -> 첫 행의 context_projection.normalize_snapshot -> 공개 상태·시각 검사
        -> subject/context + 정렬 JSON의 SHA-256 change_id -> JSON 표준 출력


  -> normalize_player_snapshot.Command.handle -> context_projection.normalize_snapshot_file
     -> read_snapshot_package -> 모든 행 normalize_snapshot
     -> write_ndjson(임시 파일) -> os.replace -> 메타데이터 JSON 표준 출력
  -> apply_player_context.Command.handle -> read_ndjson -> 모든 행 make_context_document
     -> 선택한 1-based 행 apply_context -> player_context 버전 비교 insert/replace
     -> 저장 문서 조회 + get_context -> JSON 표준 출력
  -> inspect_player_context.Command.handle -> 선택 입력 검증/저장 문서 미리보기
     -> player_context.create_index(unique media_id + subject_id)
     -> 매체/대상별 find -> JSON 표준 출력
  -> demo_context_versions.Command.handle -> 새 fixture subject 확인
     -> 고정 change 생성 -> apply_context 반복 -> 삭제 tombstone 보존
     -> get_context -> JSON 표준 출력

  -> project_player_context.Command.handle -> context_projection.project_context_file
     -> 전체 입력 검증/SHA -> checkpoint 읽기 -> 행별 apply_context
     -> Mongo 성공 후 임시 checkpoint os.replace -> 결과 JSON
  -> refresh_player_context.Command.handle -> context_projection.refresh_snapshot
     -> read_snapshot_package -> 모든 행 정규화 -> 행별 apply_context
  -> inspect_decision_context.Command.handle -> decisions.find_one
     -> get_context -> 당시/현재 context 비교 -> JSON 표준 출력

ads/management/inspect_player_context.py의 Command.handle (자동 CLI 탐색 대상 아님)
  -> player_context.create_index -> 전체 요약 필드 find -> JSON 표준 출력

mongo.get_db -> 캐시된 mongo.get_client -> MongoClient 연결 풀
```

Django 기본 인증·세션은 SQLite를 사용하고 광고 문서는 MongoDB를 사용한다. 광고 서버는 게임 Player ORM이나 Pygame 상태를 직접 읽지 않는다. 매체 서버가 보낸 공개 subject/context를 검증해 저장하며, 선택 응답 이후의 실제 표시·클릭 신호는 별도 events 요청으로 받는다.

## HTTP 메서드·전체 경로 → 함수

아래는 URLconf의 실제 접두어를 결합한 경로다. HTML 광고주 경로까지 `/api/ads/` 아래에 중복 노출되는 현재 구성을 그대로 기록한다.

| 메서드 | 실제 전체 경로 | 처리 함수/클래스 | 인증·입출력 |
|---|---|---|---|
| GET | `/api/auth/csrf/` | `auth_views.csrf_token` | CSRF 쿠키 및 JSON csrfToken |
| POST | `/api/auth/login/` | `auth_views.login_view` | CSRF, JSON username/password → 세션·authenticated |
| POST | `/api/auth/logout/` | `auth_views.logout_view` | CSRF → 세션 logout·authenticated=False |
| GET·POST | `/accounts/login/` | Django `LoginView.as_view()` | HTML form·CSRF → 로그인 redirect |
| POST·OPTIONS | `/accounts/logout/` | Django `LogoutView.as_view()` | POST에 CSRF, logout 후 redirect; GET 로그아웃 아님 |
| Django admin의 하위 경로별 | `/admin/…` | `admin.site.urls` | Django staff/admin 인증 및 자체 view |
| GET·POST | `/advertiser/campaigns/`, `/api/ads/advertiser/campaigns/` | `web_views.campaign_view` | 광고주 세션·POST CSRF → HTML |
| GET·POST | `/advertiser/bids/`, `/api/ads/advertiser/bids/` | `web_views.bid_view` | 광고주 세션·POST CSRF → HTML |
| GET | `/advertiser/events/`, `/api/ads/advertiser/events/` | `web_views.event_view` | 광고주 세션 → 본인 최근 결정·사건 HTML |
| GET | `/advertiser/reports/`, `/api/ads/advertiser/reports/` | `web_views.report_view` | 광고주 세션 → 본인 게시 일별 보고서 HTML |
| GET·POST | `/campaigns/`, `/api/ads/campaigns/` | `views.campaigns` | 광고주 세션·POST CSRF/application/json → JSON |
| GET·POST | `/bids/`, `/api/ads/bids/` | `views.bids` | 광고주 세션·POST CSRF/application/json → JSON |
| POST | `/api/media/decision/` | `views.decision` | X-Media-ID·X-Media-Key, subject/context → 광고 선택 JSON |
| POST | `/api/media/context/` | `views.context_view` | 매체 인증·subject → 현재 저장 context JSON, 미저장/삭제는 {} |
| POST | `/api/media/events/` | `views.event` | 같은 매체 인증, subject·decision_id·event_type → 사건 JSON |

Django form view가 처리하는 HEAD/OPTIONS 등 프레임워크 동작은 별도이며, 앱 decorator가 허용하는 메서드는 위 표와 같다. `/static/ads/creatives/...` 이미지 소비는 settings의 정적 파일 검색 위치와 개발 staticfiles 제공에 속하며 위 Python URLconf에 별도 path로 등록되어 있지 않다.

## 호출 계약

- **광고주 관리:** 세션 `request.user`가 소유자를 결정한다. campaigns·bids JSON API는 비로그인 401, HTML 관리 view는 `/accounts/login/`로 redirect한다. POST의 CSRF 검사는 유지된다.
- **매체 인증:** 매체 경로는 CSRF exempt이고 두 헤더를 `MEDIA_KEYS`와 비교한다. 허용 메서드 검사 → 매체 인증 → JSON/subject 검사 → view 순서다. JSON의 subject.media_id는 인증 헤더와 같아야 한다.
- **subject:** `{media_id, subject_id}` 두 문자열의 새 사전이다. 등록 매체·대상 ID 길이 1~128을 검사한다. 결정 조회는 내부 문서 전체의 필드 순서가 아니라 점 표기한 두 식별자로 비교한다.
- **선택:** `choose_ad(subject, slot_id, context)` 3인수다. 활성 매체·슬롯 후보 중 소유자가 같은 캠페인/입찰만 남긴다. bid_units 내림차순·campaign_id 오름차순으로 결정한다. context는 작은 scalar 사전으로 보존하며 순위 계산에는 사용하지 않는다.
- **선택과 표시:** decision 생성은 impression을 뜻하지 않는다. 선택은 decisions에, 표시/클릭은 ad_events에 기록된다. 과거 입찰은 현재 bids를 다시 읽어 추정하지 않고 당시 후보 스냅샷을 사용한다.
- **사건:** event_id는 `decision_id:event_type`. impression·click만 허용하고 click에는 선행 impression이 있어야 한다. 최초 created=True, 동일 사건 재전송 False. 클릭의 impression_time은 선행 노출 event_time이다.
- **시간·상태:** selected_at은 aware UTC datetime, 결정 event_time·사건 시각은 UTC ISO 문자열이다. 매체 성공 응답은 Cache-Control: no-store다. 광고 선택/사건은 게임 coins를 변경하는 코드를 호출하지 않는다.

## Mongo 문서 경계

| 컬렉션 | 키·소유자 | 현재 저장·조회 책임 |
|---|---|---|
| campaigns | `_id=campaign_id`, `owner_user_id` | repository upsert·목록, services 검증 |
| bids | `_id=bid_id=campaign_id`, `owner_user_id` | repository upsert·목록, services의 활성 소유 캠페인 검사 |
| decisions | UUID 문자열 `_id`, `subject`, 선택 후보 소유자 | choose_ad가 응답·후보·선택 시점 금액/context를 새 문서로 저장 |
| ad_events | `_id=decision_id:event_type`, `subject`, 당시 후보 소유자 | record_ad_event의 setOnInsert, 웹은 본인 decisions를 통해 조회; delivery가 file_delivered_at 갱신 |
| ad_daily_reports | JSON 배열 문자열 `[owner_user_id,campaign_id,slot_id,date]`를 `_id`로 사용 | load_ad_reports → reporting의 replace upsert; report_view → 소유자별 조회 |
| player_context | `_id=media_id:subject_id`, 고유 인덱스 `(media_id, subject_id)` | context_projection의 최신 version 반영·조회; 삭제는 tombstone, 검사 명령에서 인덱스 생성 |
| orders | save_bid_document의 반환 조회에만 등장 | 현재 저장 컬렉션 bids와 불일치하며 아래 확인 사항 참조 |

결정 스냅샷의 `owner_user_id`는 광고주 실적 화면의 조회 범위를 정한다. 사건 저장은 `chosen_campaign_id`와 일치하는 candidates 항목의 `owner_user_id`·`bid_amount`를 사용한다. 최상위 `chosen_bid_amount`만 있는 과거 결정은 후보 검증을 통과하지 못할 수 있다. 필드별 계약은 [services](files/ads/services.py.md), 오류·재전송 조건은 [events](files/ads/events.py.md)에 기록한다.

사건 실적 화면은 본인 최근 결정 30개를 읽고 각 결정의 impression·click을 각각 조회한다. 사건을 새로 만들거나 집계하지 않는다. 일별 보고서 화면은 ad_daily_reports의 본인 행을 날짜 내림차순으로 조회한다. 조회 횟수와 오류 시 템플릿 계약은 [web_views](files/ads/web_views.py.md)를 따른다.

## 관리 명령과 파일 계약

- `python ad_config/manage.py export_ad_events --output data/ad-events.ndjson [--since ISO시각] [--until ISO시각]`: 시간대가 있는 경계를 UTC로 정규화한다. 사건의 **impression_time**으로 [since, until)을 판단하고, event_time·event_id 순서로 정렬해 공개 12필드만 쓴다. 파일은 덮어쓰며 메타데이터(path·rows·sha256·schema_version·source_kind·since·until)는 표준 출력한다. [상세 계약](files/ads/exporting.py.md).
- `python ad_config/manage.py deliver_ad_events --output data/ad-events.ndjson [--limit 100]`: 표식 없는 사건을 기존 파일과 ID별 병합하고 임시 파일 교체 후 file_delivered_at을 기록한다. 한 writer를 전제로 하며 파일과 Mongo는 별도 저장 단계다. [전달 계약](files/ads/delivery.py.md).
- `python ad_config/manage.py build_ad_reports --source data/ad-events.ndjson --output data/ad-reports.ndjson`: 중복 사건 제거·클릭의 선행 노출 검증 후 서울 노출일 기준 후보를 만든다. 같은 ID의 내용 충돌은 거절한다. Mongo에 게시하지 않는다. [집계 계약](files/ads/reporting.py.md).
- `python ad_config/manage.py load_ad_reports --source data/ad-reports.ndjson`: 업무 키별 replace upsert 후 published=처리행수를 출력한다. 입력에 없는 기존 행은 유지한다. [게시 명령](files/ads/management/commands/load_ad_reports.py.md).
- `python ad_config/manage.py check_ad_reports --source data/ad-events.ndjson --output data/ad-report-check.json`: 전체 고정 입력의 재집계와 전체 게시 보고서의 키·5개 값 필드를 비교한다. JSON 증거를 저장한 뒤 불일치 시 실패 종료한다. 부분 입력은 다른 날짜 게시 행을 extra로 판정할 수 있다. [대조 계약](files/ads/management/commands/check_ad_reports.py.md).
- `/advertiser/reports/`는 로그인한 광고주의 게시된 보고서를 읽는다. 방문 시 집계·게시를 실행하지 않는다.
- `python ad_config/manage.py inspect_player_snapshot --source data/player-snapshot.ndjson`: 공개 다섯 필드와 스키마·출처·수집 시각의 정확한 여덟 필드를 검사한다. ID 중복과 수집 시각 원본 값 불일치는 거절한다. 결과는 행 수·정렬된 공개 ID·수집 시각·원본 SHA-256 등의 JSON이다. 파일·DB를 수정하지 않는다. 입력 동결과 단일 작성자를 전제로 하며 잠금은 없다. [검사 계약](files/ads/snapshot_intake.py.md).
- `python ad_config/manage.py write_cdc_readiness --output data/cdc-readiness.json [--mysql-config 경로] [--connect-home 경로] [--debezium-dir 경로]`: 세 선택 경로의 supplied·exists를 기록한다. 출력 부모 폴더를 만들고 UTF-8 JSON 파일을 덮어쓰며 같은 결과를 표준 출력한다. schema_version="cdc-readiness/v1", common_input="player-snapshot/v1"이며 mysql_binlog="not-verified", cdc_reader·connect_worker·debezium_connector·player_change_topic="not-configured", binlog_cdc_observed=False는 경로가 존재해도 유지된다. 경로의 종류·내용이나 실제 CDC 연결은 검사하지 않는다. [준비 기록 계약](files/ads/management/commands/write_cdc_readiness.py.md).

- `python ad_config/manage.py compare_player_snapshots --before data/before.ndjson --after data/after.ndjson --output data/player-compare.json`: 두 파일을 검사한 뒤 ID별 업무 상태를 비교한다. changed는 공통 ID의 room_id·coins·version·UTC updated_at 변화이며 출력에는 전후 version·coins만 담는다. newly_seen·missing_unknown은 각각 이후·이전에만 있는 ID다. 누락을 삭제로 확정하지 않으며 차이가 있어도 정상 종료한다. 결과 파일은 두 입력과 resolve 경로가 달라야 한다. [비교 명령](files/ads/management/commands/compare_player_snapshots.py.md).
- `python ad_config/manage.py write_snapshot_contract --source data/player-snapshot.ndjson --output data/player-contract.json`: 검사 결과와 source_path·UTC 생성 시각·public_fields·artifact_id="data/exports/player-cdc.ndjson" 등의 수신 메타데이터를 저장한다. 인계·미리보기·정규화·갱신의 고정 계약과 일치한다. 실제 CDC 위치는 없으며 출력은 원본과 resolve 경로가 달라야 한다. [계약 생성 명령](files/ads/management/commands/write_snapshot_contract.py.md).
- `python ad_config/manage.py write_player_change_fixture --output data/player-change-fixture.ndjson [--summary data/player-change-summary.json]`: teaching-fixture 출처의 고정 r/u/d 세 행을 저장한다. 요약은 path·source_kind·rows·sha256·interpreted이며 선택 파일과 표준 출력에 기록한다. summary를 지정하면 output과 resolve 경로가 달라야 한다. 실제 게임 상태를 수정하지 않는다. [fixture 명령](files/ads/management/commands/write_player_change_fixture.py.md).
- `python ad_config/manage.py read_snapshot_missing --before data/before.ndjson --after data/after.ndjson --output data/player-missing.json`: 두 스냅샷을 검사한 뒤 이전 파일에만 있는 정렬된 ID를 unknown으로 기록한다. source_kind="snapshot-comparison", delete_events=[], delete_inference_allowed=False이며 삭제 사건을 생성하지 않는다. 결과는 두 입력과 resolve 경로가 달라야 한다. [누락 기록 명령](files/ads/management/commands/read_snapshot_missing.py.md).
- `python ad_config/manage.py handoff_player_snapshot --source data/player-snapshot.ndjson --contract data/game-player-contract.json --target data/received/player-v2`: 검사 결과와 artifact_id="data/exports/player-cdc.ndjson"·public_fields(복수 키) 등의 기대 계약을 대조한다. target이 존재하면 거절한다. 같은 부모의 임시 폴더에 원본을 복사하고 SHA-256을 확인한 뒤 source_path를 최종 수신 파일로 바꾼 계약을 함께 저장하고 폴더를 rename한다. 최종 파일명은 player-cdc.ndjson·player-cdc-contract.json이며 rows·sha256·source_kind·target을 표준 출력한다. [인계 명령](files/ads/management/commands/handoff_player_snapshot.py.md).
- `python ad_config/manage.py preview_player_snapshot --source data/received/player-v2/player-cdc.ndjson --contract data/received/player-v2/player-cdc-contract.json [--media-id village-game]`: 계약 값·source_path와 전체 원본의 검사 결과·체크섬을 대조한 뒤 첫 행만 정규화한다. rows·source_sha256·media_id·input_preview·preview를 표준 출력하며 파일·DB를 쓰지 않는다. media-id의 기본값은 settings.ADS_MEDIA_ID다. 출력은 player-context-change/v1의 upsert와 SHA-256 change_id를 가진다. [미리보기 명령](files/ads/management/commands/preview_player_snapshot.py.md).


- `python ad_config/manage.py normalize_player_snapshot --source data/received/player-v2/player-cdc.ndjson --contract data/received/player-v2/player-cdc-contract.json --output data/player-context.ndjson [--media-id village-game]`: 수신 계약·원본을 대조하고 모든 행을 upsert로 정규화한다. 원본/계약과 같은 출력 경로를 거절하고 완성한 임시 NDJSON으로 출력 파일을 교체한다. [정규화 명령](files/ads/management/commands/normalize_player_snapshot.py.md).
- `python ad_config/manage.py apply_player_context --source data/player-context.ndjson [--row 1]`: 전체 행을 먼저 검증하고 지정한 한 행만 player_context에 반영한다. 반환 status는 applied·duplicate·stale이며 동일 version의 다른 상태는 오류다. [반영 명령](files/ads/management/commands/apply_player_context.py.md).
- `python ad_config/manage.py inspect_player_context [--source data/player-context.ndjson] [--media-id village-game] [--subject 1]`: 입력을 미리보고 고유 인덱스를 생성한 뒤 매체/대상별 저장 문서를 조회한다. source를 지정해도 문서를 반영하지 않는다. [검사 명령](files/ads/management/commands/inspect_player_context.py.md).
- `python ad_config/manage.py demo_context_versions --subject fixture-new-demo`: 존재하지 않는 fixture subject에 실제 Mongo 쓰기로 first·newer·repeat·older·conflict·delete·older-after-delete를 관찰한다. 최종 version=3 tombstone을 남긴다. [데모 명령](files/ads/management/commands/demo_context_versions.py.md).

- `python ad_config/manage.py project_player_context --source data/player-context.ndjson --checkpoint data/context-checkpoint.json [--limit 100]`: 같은 파일 SHA와 0-based next_line으로 재개한다. 전체 파일을 먼저 검증하고 각 Mongo 반영 성공 뒤 위치 파일을 교체한다. 입력이 바뀌면 기존 checkpoint를 거절한다. 현재 checkpoint 생략 시 비어 있지 않은 입력에서 위치가 증가하지 않으므로 반드시 지정한다. [일괄 반영](files/ads/management/commands/project_player_context.py.md).
- `python ad_config/manage.py refresh_player_context --source data/player-snapshot.ndjson --contract data/player-contract.json [--media-id village-game]`: 전체 계약·정규화를 마친 뒤 행별 버전 정책으로 반영한다. 누락 ID를 삭제하지 않으며 중간 실패 시 선행 반영은 남는다. [갱신 명령](files/ads/management/commands/refresh_player_context.py.md).
- `python ad_config/manage.py inspect_decision_context --subject 1 --latest [--media-id village-game]` 또는 `--decision-id ID`: 저장된 선택 당시 context와 현재 공개 복사본의 키/값 차이를 읽기만 한다. subject 조회에는 latest가 필요하고 decision-id와 latest는 함께 지정할 수 없다. [비교 명령](files/ads/management/commands/inspect_decision_context.py.md).

## 현재 구현에서 점검할 문제

1. `repository.save_bid_document()`는 bids에 저장한 뒤 orders에서 반환 문서를 읽는다. 보통 None이어서 `views.bids`의 JsonResponse에서 TypeError/500이 날 수 있다. 저장된 입찰과 HTTP 성공을 구별한다. 웹은 목록을 다시 읽어 이 결함이 덜 드러난다.
2. `choose_ad()`의 빈 광고는 `rule_version`, 선택 광고는 `policy_version`이다. 실제 키를 문서에서 임의로 통일하지 않았다.
3. settings의 SECRET_KEY·ALLOWED_HOSTS는 뒤쪽 값에 덮어쓰인다. DEBUG=True이며 비밀값 자체는 문서에 복제하지 않는다.
4. `ads.urls`가 같은 namespace로 두 번 포함된다. 광고주 HTML 경로에도 `/api/ads/` 별칭이 생기며 URL 이름 역참조 중복을 점검해야 한다.
5. 웹 `snapshot_ready`는 chosen_campaign_id 존재만 판정한다. 사건 함수는 후보 소유자·금액까지 검사하므로 웹 표시만으로 사건 저장 가능성을 확정할 수 없다. owner_user_id가 없는 과거 결정은 본인 결정 목록에도 나오지 않는다.
6. 파일 전달은 파일 교체 후 Mongo 표식을 쓰며 동시 writer를 조정하지 않는다. 표식이 있는 사건은 파일이 사라져도 재선택되지 않는다. 보고서 게시는 행별 저장이며 입력에 없는 기존 행은 유지한다.
7. 스냅샷 load_rows는 검사 후 파일을 다시 읽으므로 두 읽기 사이의 입력 불변을 전제로 한다. 비교·누락·계약·fixture JSON 출력은 직접 덮어쓰기이며 원자적 교체가 아니다. resolve 경로 비교는 서로 다른 경로의 hard link를 구별하지 않는다. handoff_snapshot은 임시 폴더를 완성한 뒤 rename하고 실패 시 임시 폴더를 정리한다.
8. build_snapshot_contract의 artifact_id·public_fields가 인계·미리보기 소비 조건과 일치하도록 수정되었다. handoff_snapshot은 Python ==, read_snapshot_package는 JSON 표현으로 대조하므로 타입 구별 정도는 여전히 다르다. 수신 계약의 source_path는 최종 입력 파일을 가리켜야 한다.
9. 정규화 미리보기는 파일 순서의 첫 행만 처리한다. player_id·subject_id는 문자열이며 captured_at은 검사하지만 change_id에 포함하지 않는다. 미리보기 자체는 저장하지 않는다. 전체 정규화·선택 행 Mongo 반영은 별도 명령이며 저장 context가 광고 순위 계산에 연결되지는 않는다. player-snapshot은 upsert만 허용하고 teaching-fixture만 명시적 delete를 허용한다.
10. make_context_document의 context 분기는 op=="deleted"를 비교하지만 검증에서 허용한 op는 upsert/delete다. 항상 입력 context를 복사하며 delete의 빈 사전은 선행 검증으로 보장된다. 동일 version의 중복 판정은 deleted/context만 비교한다. inspect_player_context는 조회에 앞서 고유 인덱스를 생성하며 데모는 저장 데이터를 남긴다.
11. project_context_file은 checkpoint가 있을 때만 position을 증가시킨다. checkpoint 생략 시 비어 있지 않은 입력은 반복 처리하며 종료하지 않는다. 체크포인트 사용 시에도 Mongo와 위치 파일은 별도 단계이며 동시 writer 잠금은 없다.
12. 현재 tests.py는 기본 골격이다. 이 문서는 정적 호출/시그니처 문서이며 실제 HTTP·Mongo 실행 성공을 증명하는 테스트 결과가 아니다.

## 문서 갱신 규칙

1. 런타임 Python 파일을 추가·이동·삭제하면 프로젝트 상대경로를 보존한 `files/<경로>.md`를 함께 갱신한다. 테스트·migrations·빈 __init__ 제외 기준도 유지한다.
2. `audit_routing.py`의 AST inventory로 실제 클래스·함수·직접 정의한 메서드와 signature를 먼저 추출한다. annotation·기본값·가변인자까지 소스 signature 그대로 기록한다.
3. 각 기호는 **signature → 검증/변환 → 직접 호출 → 반환/상태** 순서로 설명한다. 다른 계층 내부를 복제하지 않고 관련 파일 문서로 연결한다.
4. URLconf·decorator·응답 키가 바뀌면 전체 메서드/경로 표와 호출 트리·값 계약을 함께 고친다. 수업 다운로드 자료나 계획만으로 구현됐다고 기재하지 않는다.
5. 문서 검증은 파일 대응·signature·링크·호출 의미를 확인한다. 런타임 검증이 필요한 변경은 별도 실행 증거를 남긴다. `.env`·쿠키·실제 매체 키·계정 정보는 문서에 넣지 않는다.

## 이번 점검 결과

2026-10-13 기준 직전 커밋 6a75121과 작업 트리를 대조해 새 관리 명령 3개·context_projection 함수 5개·context 조회 API와 계약 필드 수정을 반영했다. 런타임 45파일·129개 기호(함수/클래스 88개·직접 정의 메서드 41개)의 AST 시그니처·파일 대응·문서 링크를 확인했다. 변경사항 감사의 문서 누락·오래된 문서·파싱 오류·미기재 기호·인수 구조 불일치는 0건이다. 새 관리 명령 3개의 help가 로딩되었고 Django 시스템 검사에는 기존 urls.W005 경고가 남는다. 체크포인트 생략 시 위치가 증가하지 않는 현재 코드의 제한을 명시했다. 실제 Mongo 반영·HTTP·CDC 실행은 수행하지 않았다.
