import json
from django.core.management.base import BaseCommand
from ads.exporting import export_ad_events


class Command(BaseCommand):
    help = "공개 광고 사건을 [since, until) NDJSON으로 내보냅니다."

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)
        parser.add_argument("--since")
        parser.add_argument("--until")

    def handle(self, *args, **options):
        result = export_ad_events(options["output"], options["since"], options["until"])
        self.stdout.write(json.dumps(result, ensure_ascii=False))
