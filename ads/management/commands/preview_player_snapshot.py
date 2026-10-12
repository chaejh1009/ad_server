import json
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from ads.context_projection import read_snapshot_package, normalize_snapshot


class Command(BaseCommand):
    help = "수신 계약을 확인하고 정규화 결과 첫 행을 화면에 보여줍니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--contract", required=True)
        parser.add_argument("--media-id", default=settings.ADS_MEDIA_ID)

    def handle(self, *args, **options):
        try:
            if not options["media_id"].strip():
                raise ValueError("media_id는 비어 있지 않은 문자열이어야 합니다.")
            rows, inspected = read_snapshot_package(options["source"], options["contract"])
            preview = [normalize_snapshot(row, media_id=options["media_id"])
                       for row in rows[:1]]
        except (OSError, TypeError, ValueError, KeyError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps({"rows": len(rows), "source_sha256": inspected["sha256"],
                                      "media_id": options["media_id"],
                                      "input_preview": rows[:1], "preview": preview},
                                     ensure_ascii=False, sort_keys=True, indent=2))