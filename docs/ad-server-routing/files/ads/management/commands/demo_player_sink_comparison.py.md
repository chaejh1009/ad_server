# `ads/management/commands/demo_player_sink_comparison.py`

원본 소스 경로: `ads/management/commands/demo_player_sink_comparison.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

별도 메모리 fixture로 공개 상태 대조의 정상·차이·거절을 관찰한다. [대조 함수](../../sink_evidence.py.md)와 [fixture](demo_player_lake.py.md)를 사용한다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django 관리 명령 로더 → add_arguments·handle.
3. **반환·상태:** 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --case 필수: same·missing·newer·extra·duplicate·invalid 중 하나다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하고 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** 등록된 옵션을 받아 다음 계약을 적용한다.
2. **직접 호출:** fixture_change → make_context_document → case별 actual 구성 → extra 대상의 stable_json·SHA 재생성 → compare_rows → stdout.write.
3. **반환·상태:** teaching-fixture·case·database_changed=False와 대조 결과를 출력한다. same은 일치, missing/newer는 입력 범위 불일치, extra는 추가 키와 입력 범위 일치를 반환한다. duplicate/invalid는 CommandError로 실패한다. ValueError·KeyError·TypeError를 변환하며 파일·DB는 수정하지 않는다.
