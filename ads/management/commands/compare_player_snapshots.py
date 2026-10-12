import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ads.snapshot_intake import compare, load_rows


class Command(BaseCommand):
    help = "동결된 두 파일의 공개 상태를 ID 기준으로 비교합니다."

    def add_arguments(self, parser):
        parser.add_argument("--before", required=True)
        parser.add_argument("--after", required=True)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        try:
            result = compare(load_rows(options["before"]), load_rows(options["after"]))
            target = Path(options["output"])
            if target.resolve() in {Path(options["before"]).resolve(), Path(options["after"]).resolve()}:
                raise ValueError("비교 결과는 원본과 다른 경로에 저장하세요.")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                              encoding="utf-8")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))