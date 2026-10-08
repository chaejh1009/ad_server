from django.core.management.base import BaseCommand
from ads.exporting import read_ndjson
from ads.reporting import publish_reports


class Command(BaseCommand):
    help = "보고서 후보의 업무 키만 게시합니다. 다른 날짜 행은 유지합니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)

    def handle(self, *args, **options):
        count = publish_reports(read_ndjson(options["source"]))
        self.stdout.write(f"published={count}")