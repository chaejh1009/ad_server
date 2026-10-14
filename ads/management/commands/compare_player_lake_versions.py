import hashlib
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


def read_lake_manifest(folder):
    root = Path(folder)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest["schema_version"] != "player-lake/v1":
        raise ValueError("player-lake/v1 manifest가 필요합니다.")
    for name in ("history", "current"):
        record = manifest["files"][name]
        if record["path"] != name + ".ndjson":
            raise ValueError("결과 파일명이 다릅니다.")
        payload = (root / record["path"]).read_bytes()
        if hashlib.sha256(payload).hexdigest() != record["sha256"]:
            raise ValueError("저장 파일과 manifest의 SHA가 다릅니다.")
        if len(payload.splitlines()) != record["rows"]:
            raise ValueError("저장 파일과 manifest의 행 수가 다릅니다.")
    return manifest


class Command(BaseCommand):
    help = "보존한 두 Lake 버전의 입력·결과 파일 지문을 대조합니다."

    def add_arguments(self, parser):
        parser.add_argument("--before", required=True)
        parser.add_argument("--after", required=True)

    def handle(self, *args, **options):
        try:
            before = read_lake_manifest(options["before"])
            after = read_lake_manifest(options["after"])
            result = {"before": options["before"], "after": options["after"],
                      "source_matches": before["source_sha256"] == after["source_sha256"],
                      "history_matches": before["files"]["history"] == after["files"]["history"],
                      "current_matches": before["files"]["current"] == after["files"]["current"],
                      "before_counts": {name: before[name] for name in ("input_rows", "history_rows", "current_rows")},
                      "after_counts": {name: after[name] for name in ("input_rows", "history_rows", "current_rows")}}
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False))