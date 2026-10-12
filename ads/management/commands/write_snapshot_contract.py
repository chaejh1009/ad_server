import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ads.snapshot_intake import build_snapshot_contract


class Command(BaseCommand):
    help = "검사한 파일의 행 수·ID·체크섬을 인계 계약으로 저장합니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        try:
            result = build_snapshot_contract(options["source"])
            target = Path(options["output"])
            if target.resolve() == Path(options["source"]).resolve():
                raise ValueError("계약 파일과 원본 파일의 경로를 다르게 지정하세요.")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                              encoding="utf-8")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))