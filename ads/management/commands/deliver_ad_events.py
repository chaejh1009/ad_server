import json
from django.core.management.base import BaseCommand
from ads.delivery import deliver_events


class Command(BaseCommand):
    help = "광고 실적을 한 writer의 로컬 파일로 전달합니다."

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        result = deliver_events(options["output"], options["limit"])
        self.stdout.write(json.dumps(result, ensure_ascii=False))