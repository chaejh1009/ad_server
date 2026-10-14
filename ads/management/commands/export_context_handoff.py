import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pymongo.errors import PyMongoError

from ads.context_projection import export_context_handoff


class Command(BaseCommand):
    help = "검증한 입력·완료 기록·현재 공개 복사본을 새 인계 폴더로 묶습니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--checkpoint", required=True)
        parser.add_argument("--output-dir", required=True)
        parser.add_argument("--media-id", default=settings.ADS_MEDIA_ID)

    def handle(self, *args, **options):
        try:
            result = export_context_handoff(options["source"], options["checkpoint"],
                                            options["output_dir"], options["media_id"])
        except (OSError, ValueError, TypeError, KeyError, PyMongoError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False))