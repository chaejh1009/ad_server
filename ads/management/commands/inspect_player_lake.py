import hashlib
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from ads.context_projection import _read_context_changes, _read_context_checkpoint
from ads.lake_files import build_history, stable_json


class Command(BaseCommand):
    help = "고정 입력의 history/current를 저장 없이 미리 봅니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--manifest")
        parser.add_argument("--stage", choices=("history", "current"), default="history")
        parser.add_argument("--repeat", type=int, default=1)
        parser.add_argument("--reverse", action="store_true")

    def handle(self, *args, **options):
        try:
            if options["repeat"] < 1:
                raise ValueError("repeat는 양수 정수입니다.")
            rows, checksum = _read_context_changes(options["source"])
            if options["manifest"]:
                manifest = json.loads(Path(options["manifest"]).read_text(encoding="utf-8"))
                if (manifest["input_sha256"] != checksum
                        or manifest["input_rows"] != len(rows)
                        or manifest["input_schema_version"] != "player-context-change/v1"
                        or manifest["source_kind"] != "player-snapshot"):
                    raise ValueError("인계 manifest와 입력이 다릅니다.")
                if any(row["media_id"] != manifest["media_id"]
                       or row["source_kind"] != manifest["source_kind"] for row in rows):
                    raise ValueError("인계 매체·출처와 입력이 다릅니다.")
                position = _read_context_checkpoint(
                    manifest["checkpoint_path"], checksum, len(rows))
                if position != len(rows):
                    raise ValueError("인계 checkpoint가 완료되지 않았습니다.")
            supplied = rows * options["repeat"]
            if options["reverse"]:
                supplied = list(reversed(supplied))
            history = build_history(supplied)
            result_rows = history
            if options["stage"] == "current":
                from ads.lake_files import build_current
                result_rows = build_current(history)
            result = {
                "stage": options["stage"], "source": str(options["source"]),
                "source_sha256": checksum, "input_rows": len(rows),
                "supplied_rows": len(supplied), "history_rows": len(history),
                "result_rows": len(result_rows),
                "result_sha256": hashlib.sha256(stable_json(result_rows).encode("utf-8")).hexdigest(),
                "preview": result_rows[:1], "written": False,
            }
        except (OSError, ValueError, TypeError, KeyError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False))