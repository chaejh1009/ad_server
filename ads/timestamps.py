from datetime import datetime, timezone


def parse_utc(value):
    instant = datetime.fromisoformat(value)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("시간대가 있는 ISO 시각을 사용하세요.")
    return instant.astimezone(timezone.utc)