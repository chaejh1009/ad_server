import json

from django.core.management.base import BaseCommand, CommandError

from ads.snapshot_intake import handoff_snapshot


class Command(BaseCommand):
    help = "검증한 원본과 계약을 새 수신 폴더에 함께 인계합니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--contract", required=True)
        parser.add_argument("--target", required=True)

    def handle(self, *args, **options):
        try:
            result = handoff_snapshot(options["source"], options["contract"], options["target"])
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))