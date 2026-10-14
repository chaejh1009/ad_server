import hashlib
import json

from django.core.management.base import BaseCommand, CommandError
from ads.lake_files import build_history, stable_json

def fixture_change(version, coins=10, op="upsert"):
    when = f"2026-10-14T00:00:{version:02d}+00:00"
    context = {} if op == "delete" else {
        "player_id": "fixture-lake", "room_id": "square", "coins": coins,
        "version": version, "updated_at": when,
    }
    row = {"schema_version": "player-context-change/v1", "source_kind": "teaching-fixture",
           "media_id": "village-game", "subject_id": "fixture-lake", "op": op,
           "version": version, "event_time": when, "context": context}
    row["change_id"] = hashlib.sha256(stable_json(row).encode("utf-8")).hexdigest()
    return row

class Command(BaseCommand):
    help = "메모리의 별도 fixture로 Lake 중복·버전·삭제·거절을 관찰합니다."

    def add_arguments(self, parser):
        parser.add_argument("--case", required=True, choices=(
            "duplicates", "invalid-schema", "change-id-conflict", "versions",
            "delete", "version-conflict", "empty"))

    def handle(self, *args, **options):
        case = options["case"]
        rows = [fixture_change(1), fixture_change(4, 40), fixture_change(2, 20)]
        if case == "duplicates":
            rows = [rows[0], rows[0], rows[1]]
        elif case == "invalid-schema":
            rows[0]["schema_version"] = "ad-event/v1"
        elif case == "change-id-conflict":
            changed = fixture_change(1, 99)
            changed["change_id"] = rows[0]["change_id"]
            rows = [rows[0], changed]
        elif case == "delete":
            rows = [fixture_change(4, op="delete"), fixture_change(2, 20)]
        elif case == "version-conflict":
            rows = [fixture_change(4, 40), fixture_change(4, 99)]
        elif case == "empty":
            rows = []
        try:
            history = build_history(rows)
            current = []
            if case != "duplicates":
                from ads.lake_files import build_current
                current = build_current(history)
            result = {"case": case, "source_kind": "teaching-fixture",
                      "input_rows": len(rows), "history_rows": len(history),
                      "current_rows": len(current), "current": current,
                      "written": False, "database_changed": False}
        except (ValueError, TypeError, KeyError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False))

