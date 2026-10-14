# `ads/sink_evidence.py`

원본 소스 경로: `ads/sink_evidence.py` · [전체 라우팅](../../README.md)

## 책임과 경계

Lake current와 Mongo 공개 문서의 입력 대상 상태를 검증·대조한다. [context_projection](context_projection.py.md)의 문서 계약을 사용하며 Mongo 조회 외 저장은 없다.

## `def _index_context_rows(rows)`

Signature: `def _index_context_rows(rows)`

1. **검증·변환:** 정확한 공개 9필드 또는 schema_version을 더한 10필드 dict만 허용한다. 추가 schema는 player-current/v1, deleted는 bool이어야 한다. 변경 사전으로 재구성해 공개 문서·해시를 대조하고 _id 중복을 거절한다.
2. **직접 호출:** make_context_document → 공개 문서 비교 → _id별 사전 구성.
3. **반환·상태:** _id를 키로 원래 행을 담은 사전을 반환한다. 추가 schema 존재 여부는 정규화 계약 검사 후 비교값에 영향을 주지 않는다. ValueError·KeyError·TypeError 등 계약 오류를 전파한다.

## `def compare_rows(expected_rows, actual_rows)`

Signature: `def compare_rows(expected_rows, actual_rows)`

1. **검증·변환:** 양쪽 전체 목록을 _index_context_rows로 검사한다. 공통 키의 media_id·subject_id·version·deleted·context 다섯 필드만 비교한다.
2. **직접 호출:** _index_context_rows(양쪽) → 키 차집합/교집합 sorted → 필드 차이 → matched 계산.
3. **반환·상태:** expected_keys·missing·extra_keys·mismatched·matched·input_scope_matches를 반환한다. 불일치에는 _id·fields·values의 lake/mongo 값을 기록한다. 추가 실제 키만 있으면 input_scope_matches=True이며 누락 또는 불일치는 False다. source_kind·change_id·event_time은 계약 검사는 하지만 일치 비교 필드는 아니다. 차이 자체로 예외를 발생시키지 않고 저장하지 않는다.

## `def compare_context_to_current(current_rows, media_id='village-game')`

Signature: `def compare_context_to_current(current_rows, media_id='village-game')`

1. **검증·변환:** current 각 행의 media_id가 지정 매체와 같아야 한다. 빈 목록은 허용한다.
2. **직접 호출:** get_db()["player_context"].find({media_id}) → compare_rows.
3. **반환·상태:** 지정 매체의 전체 Mongo 문서를 읽어 compare_rows 결과를 반환한다. 입력 밖 대상은 extra_keys로 남긴다. DB 수정·일관된 스냅샷 잠금은 없으며 Mongo 오류를 전파한다.
