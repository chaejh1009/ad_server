# `ads/management/commands/refresh_player_context.py`

원본 소스 경로: `ads/management/commands/refresh_player_context.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

새 수신 스냅샷 전체를 정규화하여 최신 Mongo context에 반영한다. 누락 ID를 삭제하지 않는다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속한다.
2. **직접 호출:** Django가 옵션 등록과 handle을 호출한다.
3. **반환·상태:** 관리 명령 진입점을 정의한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --source·--contract 필수, --media-id 기본값 settings.ADS_MEDIA_ID다.
2. **직접 호출:** parser.add_argument.
3. **반환·상태:** parser를 변경하며 명시적 반환값은 없다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** OSError·ValueError·TypeError·KeyError·PyMongoError를 CommandError로 변환한다. 수신 계약과 모든 스냅샷 행 정규화는 저장 전에 완료한다.
2. **직접 호출:** refresh_snapshot → json.dumps(ensure_ascii=False, sort_keys=True, indent=2) → stdout.write.
3. **반환·상태:** source·contract·rows·source_sha256·media_id·counts·첫 정규화 행 preview를 출력한다. 체크포인트는 없으며 중간 실패 시 이미 반영한 행은 남는다.
