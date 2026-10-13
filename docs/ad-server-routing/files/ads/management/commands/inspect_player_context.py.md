# `ads/management/commands/inspect_player_context.py`

원본 소스 경로: `ads/management/commands/inspect_player_context.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

정규화 입력을 저장 문서로 미리보고 현재 Mongo 상태를 조회한다. 문서 반영은 하지 않지만 고유 인덱스를 생성한다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django가 옵션 등록과 handle을 호출한다.
3. **반환·상태:** 관리 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source·--subject 선택, --media-id 기본값 settings.ADS_MEDIA_ID다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하며 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** subject 미지정 시 검사용 "inspect"로 키를 검사한다. 파일의 모든 행을 검증하고 입력 media_id와 옵션이 다르면 거절한다. 기존 중복 자료로 인덱스 생성이 실패할 수 있다. OSError·TypeError·ValueError·KeyError·PyMongoError를 CommandError로 변환한다.
2. **직접 호출:** context_subject_key → 선택 입력의 read_ndjson/make_context_document → get_db → create_index → find(query).sort("_id", 1) → index_information → json.dumps → stdout.write.
3. **반환·상태:** player_context에 (media_id, subject_id) unique 인덱스 media_subject_once를 생성한다. 매체별 조회이며 subject 지정 시 _id로 제한한다. database·count·index·rows·input_rows·document_preview(최대 첫 행)를 들여쓰기 JSON으로 출력한다. source 생략 시 input_rows=None, preview=[]다.
