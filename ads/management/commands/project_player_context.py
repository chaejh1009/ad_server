import json

from django.core.management.base import BaseCommand, CommandError
from pymongo.errors import PyMongoError

from ads.context_projection import project_context_file


class Command(BaseCommand):
    help = "같은 정규화 입력과 checkpoint로 중지·재개하며 전체 context를 반영합니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--checkpoint")
        parser.add_argument("--limit", type=int)

    def handle(self, *args, **options):
        try:
            result = project_context_file(options["source"], options["checkpoint"], options["limit"])
        except (OSError, ValueError, TypeError, KeyError, PyMongoError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False))