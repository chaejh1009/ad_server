# `ads/timestamps.py`

원본 소스 경로: `ads/timestamps.py` · [전체 라우팅](../../README.md)

## 책임과 경계

내보내기에서 시간대가 있는 ISO 시각을 UTC로 정규화한다. DB를 사용하지 않는다.

## `def parse_utc(value)`

Signature: `def parse_utc(value)`

1. **검증·변환:** datetime.fromisoformat(value)로 파싱하고 tzinfo 또는 utcoffset이 없으면 ValueError를 발생시킨다. 잘못된 형식의 파싱 오류도 전파한다.
2. **직접 호출:** datetime.fromisoformat → instant.astimezone(timezone.utc).
3. **반환·상태:** aware UTC datetime을 반환한다. 호출자는 [exporting](exporting.py.md)이며 reporting은 현재 import만 한다.
