import json

from django.core.management.base import BaseCommand, CommandError
from ads.lake_files import build_lake_version


class Command(BaseCommand):
    help = "고정 입력에서 새 NDJSON Player Lake 버전을 만듭니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        try:
            result = build_lake_version(options["source"], options["output"])
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False))