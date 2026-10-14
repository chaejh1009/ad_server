import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pymongo.errors import PyMongoError

from ads.context_projection import _read_context_changes
from ads.exporting import read_ndjson
from ads.lake_files import build_history, build_current
from ads.sink_evidence import compare_context_to_current
from ads.management.commands.compare_player_lake_versions import read_lake_manifest



class Command(BaseCommand):
    help = "같은 원본·검증한 Lake와 지정 매체 Mongo 공개 상태를 대조합니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--lake-dir", required=True)
        parser.add_argument("--output", required=True)
        parser.add_argument("--media-id", default=settings.ADS_MEDIA_ID)

    def handle(self, *args, **options):
        try:
            source = Path(options["source"])
            lake_dir = Path(options["lake_dir"])
            output = Path(options["output"])
            protected = [source, lake_dir / "manifest.json",
                         lake_dir / "history.ndjson", lake_dir / "current.ndjson"]
            if output.resolve() in {path.resolve() for path in protected} or any(
                    output.exists() and path.exists() and output.samefile(path) for path in protected):
                raise ValueError("출력은 원본·Lake 파일과 다른 경로여야 합니다.")
            lake = read_lake_manifest(lake_dir)
            rows, checksum = _read_context_changes(source)
            if checksum != lake["source_sha256"] or len(rows) != lake["input_rows"]:
                raise ValueError("Lake와 지정 원본의 SHA·행 수가 다릅니다.")
            history = build_history(rows)
            expected = build_current(history)
            current = read_ndjson(lake_dir / "current.ndjson")
            if read_ndjson(lake_dir / "history.ndjson") != history or current != expected:
                raise ValueError("Lake 결과가 지정 원본의 변환 결과와 다릅니다.")
            compared = compare_context_to_current(current, options["media_id"])
            result = {"source_path": str(source), "source_sha256": checksum,
                      "lake_dir": str(lake_dir), "media_id": options["media_id"],
                      "lake_current_sha256": lake["files"]["current"]["sha256"],
                      "same_source_verified": True, **compared}
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            result["path"] = str(output)
        except (OSError, ValueError, KeyError, TypeError, PyMongoError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False))