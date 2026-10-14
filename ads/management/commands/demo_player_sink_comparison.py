import hashlib
import json

from django.core.management.base import BaseCommand, CommandError
from ads.context_projection import make_context_document
from ads.lake_files import stable_json
from ads.management.commands.demo_player_lake import fixture_change
from ads.sink_evidence import compare_rows


class Command(BaseCommand):
    help = "별도 메모리 fixture로 공개 상태 대조의 정상·차이를 확인합니다."

    def add_arguments(self, parser):
        parser.add_argument("--case", required=True,
                            choices=("same", "missing", "newer", "extra", "duplicate", "invalid"))

    def handle(self, *args, **options):
        try:
            expected = [make_context_document(fixture_change(2, 20))]
            actual = list(expected)
            case = options["case"]
            if case == "missing":
                actual = []
            elif case == "newer":
                actual = [make_context_document(fixture_change(4, 40))]
            elif case == "extra":
                change = fixture_change(1)
                change["subject_id"] = change["context"]["player_id"] = "fixture-extra"
                change["change_id"] = hashlib.sha256(stable_json(
                    {name: value for name, value in change.items() if name != "change_id"}
                ).encode("utf-8")).hexdigest()
                actual.append(make_context_document(change))
            elif case == "duplicate":
                actual = actual + actual
            elif case == "invalid":
                expected = actual = [{"_id": "bogus"}]
            result = {"case": case, "source_kind": "teaching-fixture",
                      "database_changed": False, **compare_rows(expected, actual)}
        except (ValueError, KeyError, TypeError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False))