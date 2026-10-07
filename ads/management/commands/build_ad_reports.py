import json
from django.core.management.base import BaseCommand
from ads.exporting import read_ndjson, write_ndjson
from ads.reporting import build_daily_reports


class Command(BaseCommand):
    help = "고정 광고 NDJSON에서 일별 보고서 후보를 계산합니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        rows = build_daily_reports(read_ndjson(options["source"]))
        checksum = write_ndjson(options["output"], rows)
        self.stdout.write(json.dumps({"rows": len(rows), "sha256": checksum,
                                    "path": options["output"]}, ensure_ascii=False))