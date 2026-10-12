import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ads.snapshot_intake import readiness


class Command(BaseCommand):
    help = "경로 존재와 CDC 미구성 상태를 분리한 준비 기록을 저장합니다."

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)
        parser.add_argument("--mysql-config")
        parser.add_argument("--connect-home")
        parser.add_argument("--debezium-dir")

    def handle(self, *args, **options):
        try:
            result = readiness(options.get("mysql_config"), options.get("connect_home"),
                               options.get("debezium_dir"))
            target = Path(options["output"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                              encoding="utf-8")
        except (OSError, ValueError, TypeError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True))