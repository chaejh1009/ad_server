import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pymongo.errors import PyMongoError

from ads.context_projection import refresh_snapshot


class Command(BaseCommand):
    help = "새 snapshot과 수신 계약을 대조한 뒤 공개 context를 갱신합니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--contract", required=True)
        parser.add_argument("--media-id", default=settings.ADS_MEDIA_ID)

    def handle(self, *args, **options):
        try:
            result = refresh_snapshot(options["source"], options["contract"],
                                      media_id=options["media_id"])
        except (OSError, ValueError, TypeError, KeyError, PyMongoError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))