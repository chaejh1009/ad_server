import json

from django.core.management.base import BaseCommand, CommandError

from ads.snapshot_intake import inspect_snapshot


class Command(BaseCommand):
    help = "저장된 플레이어 공개 스냅샷을 검사합니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)

    def handle(self, *args, **options):
        try:
            result = inspect_snapshot(options["source"])
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True))