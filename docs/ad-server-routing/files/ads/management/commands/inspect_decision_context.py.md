# `ads/management/commands/inspect_decision_context.py`

원본 소스 경로: `ads/management/commands/inspect_decision_context.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

선택 당시 decisions.context와 현재 player_context를 읽어 비교한다. 저장·인덱스 생성을 수행하지 않는다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django가 옵션 등록과 handle을 호출한다.
3. **반환·상태:** 관리 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --decision-id 또는 --subject 중 하나 필수다. --latest는 store_true, --media-id 기본값 settings.ADS_MEDIA_ID다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하며 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** --decision-id와 --latest 동시 지정, 빈 decision ID, --subject에 --latest 생략, 선택 기록 부재를 거절한다. 매체 ID를 조회 필터에 포함한다. empty 선택은 이력이 없다. ValueError·TypeError·KeyError·PyMongoError를 CommandError로 변환한다.
2. **직접 호출:** context_subject_key → decisions.find_one(query, projection, sort=[selected_at 내림차순, _id 내림차순]) → get_context → 차이 사전 구성 → JSON 표준 출력.
3. **반환·상태:** decision_id·subject·selected_at·context·current_context·same_context·differences를 출력한다. selected_at이 isoformat을 제공하면 문자열로 바꾼다. 차이는 키 합집합을 정렬하여 값 또는 키 존재 여부가 다를 때 decision/current 값을 기록한다. 키 누락과 null 차이도 검출한다.
