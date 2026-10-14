from .mongo import get_db
from .context_projection import make_context_document

COMPARE_FIELDS = ("media_id", "subject_id", "version", "deleted", "context")


def _index_context_rows(rows):
    fields = {"_id", "media_id", "subject_id", "version", "deleted", "context",
              "source_kind", "change_id", "event_time"}
    indexed = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) not in (fields, fields | {"schema_version"}):
            raise ValueError("대조 문서의 공개 필드 계약이 다릅니다.")
        if "schema_version" in row and row["schema_version"] != "player-current/v1":
            raise ValueError("player-current/v1 문서가 필요합니다.")
        if type(row["deleted"]) is not bool:
            raise ValueError("deleted는 bool이어야 합니다.")
        document = {name: row[name] for name in fields}
        change = {"schema_version": "player-context-change/v1",
                  "op": "delete" if row["deleted"] else "upsert",
                  **{name: row[name] for name in fields - {"_id", "deleted"}}}
        if make_context_document(change) != document:
            raise ValueError("대조 문서의 키·공개 상태·변경 ID가 다릅니다.")
        if row["_id"] in indexed:
            raise ValueError("duplicate subject key")
        indexed[row["_id"]] = row
    return indexed

def compare_rows(expected_rows, actual_rows):
    # [문제 1 · 여러 줄] 양쪽 목록의 계약을 검사해 키별 사전으로 만든다. (2줄)
    # 예시: required = index_records(required_rows)
    #       received = index_records(received_rows)
    expected = _index_context_rows(expected_rows)
    actual = _index_context_rows(actual_rows)

    # [문제 2 · 여러 줄] 누락 키와 입력 밖 추가 키를 각각 구한다. (2줄)
    # 예시: absent = sorted(set(required) - set(received))
    #       surplus = sorted(set(received) - set(required))
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))

    mismatched = []
    # [문제 3 · 한 단어] 양쪽 공통 키의 비교 순서를 고정하는 함수다.
    for key in sorted(set(expected) & set(actual)):

        # [문제 4 · 한 줄] 같은 키의 다섯 비교 필드 중 다른 필드를 모은다.
        # 예시: changed = [name for name in names if left[code][name] != right[code][name]]
        fields = [name for name in COMPARE_FIELDS if expected[key][name] != actual[key][name]]

        if fields:
            # [문제 5 · 여러 줄] 키·다른 필드·양쪽 값을 불일치 목록에 기록한다. (3줄)
            # 예시: changes.append({"code": code, "names": changed,
            #                       "values": {name: {"left": left[code][name], "right": right[code][name]}
            #                                  for name in changed}})
            mismatched.append({"_id": key, "fields": fields,
                            "values": {name: {"lake": expected[key][name], "mongo": actual[key][name]}
                                        for name in fields}})

    # [문제 6 · 한 줄] 입력 대상 수에서 누락·불일치 대상 수를 빼 일치 수를 구한다.
    # 예시: passed = len(required) - len(absent) - len(changed_records)
    matched = len(expected) - len(missing) - len(mismatched)

    return {"expected_keys": len(expected), "missing": missing, "extra_keys": extra,
            "mismatched": mismatched, "matched": matched,
            "input_scope_matches": not missing and not mismatched}

def compare_context_to_current(current_rows, media_id="village-game"):
    # 동일 입력의 키만 일치 기준이며 이전 입력의 추가 키는 따로 기록한다.
    if any(row.get("media_id") != media_id for row in current_rows):
        raise ValueError("current와 지정 매체가 다릅니다.")
    actual = list(get_db()["player_context"].find({"media_id": media_id}))
    return compare_rows(current_rows, actual)
