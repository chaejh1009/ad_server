import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ads.snapshot_intake import change_player, write_ndjson


class Command(BaseCommand):
    help = "실제 CDC와 구별한 r/u/d 교육 fixture와 해석 결과를 저장합니다."

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)
        parser.add_argument("--summary")

    def handle(self, *args, **options):
        original = {"id": 1, "room_id": "room-01", "coins": 0, "version": 0,
                    "updated_at": "2026-10-08T00:00:00+00:00"}
        updated = {**original, "coins": 30, "version": 1,
                   "updated_at": "2026-10-08T00:01:00+00:00"}
        events = [
            {"source_kind": "teaching-fixture", "op": "r", "before": None, "after": original},
            {"source_kind": "teaching-fixture", "op": "u", "before": original, "after": updated},
            {"source_kind": "teaching-fixture", "op": "d", "before": updated, "after": None},
        ]
        try:
            if options.get("summary") and Path(options["summary"]).resolve() == Path(options["output"]).resolve():
                raise ValueError("fixture 원문과 summary는 다른 경로에 저장하세요.")
            interpreted = [change_player(event) for event in events]
            checksum = write_ndjson(options["output"], events)
            result = {"path": str(options["output"]), "source_kind": "teaching-fixture",
                      "rows": len(events), "sha256": checksum, "interpreted": interpreted}
            if options.get("summary"):
                target = Path(options["summary"])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                                  encoding="utf-8")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True))