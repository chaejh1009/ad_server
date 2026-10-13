import json
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from ads.context_projection import normalize_snapshot_file


class Command(BaseCommand):
    help = "수신 계약을 확인하고 공개 상태의 context 변경 파일을 작성합니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--contract", required=True)
        parser.add_argument("--output", required=True)
        parser.add_argument("--media-id", default=settings.ADS_MEDIA_ID)

    def handle(self, *args, **options):
        try:
            result = normalize_snapshot_file(options["source"], options["contract"],
                                             options["output"], media_id=options["media_id"])
        except (OSError, TypeError, ValueError, KeyError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))