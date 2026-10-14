import json
import hashlib
import tempfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from pymongo.errors import PyMongoError

from ads.exporting import EVENT_FIELDS, export_ad_events, read_ndjson



class Command(BaseCommand):
    help = '광고 사건을 새 고정 파일로 내보내고 ID·schema·SHA를 확인합니다.'

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)
        parser.add_argument("--since")
        parser.add_argument("--until")

    def handle(self, *args, **options):
        try:
            path = Path(options["output"])
            # [문제 1 · 여러 줄] 이미 있는 원본 경로를 오류로 거절한다. (2줄)
            # 예시: if destination.exists():
            #           raise ValueError("choose a new path")
            if path.exists():
                raise ValueError("choose a new path")

            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=".ad-export-", dir=path.parent) as folder:
                staged = Path(folder) / "events.ndjson"
                # [문제 2 · 한 줄] 기존 export 함수를 임시 경로·시작·끝으로 호출한다.
                # 예시: result = export_records(temporary, lower, upper)
                exported = export_ad_events(staged, options["since"], options["until"])

                rows = read_ndjson(staged)
                if any(set(row) != set(EVENT_FIELDS) or row["schema_version"] != "ad-event/v1" for row in rows):
                    raise ValueError("ad-event/v1의 정확한 공개 필드가 필요합니다.")
                # [문제 3 · 여러 줄] ID를 모으고 중복이 있으면 거절한다. (3줄)
                # 예시: codes = [item["code"] for item in entries]
                #       if len(codes) != len(set(codes)):
                #           raise ValueError("duplicate code")
                ids = [row["event_id"] for row in rows]
                if len(ids) != len(set(ids)):
                    raise ValueError("duplicate code")

                # [문제 4 · 여러 줄] 임시 파일 SHA를 계산하고 기존 반환 SHA와 대조한다. (3줄)
                # 예시: digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
                #       if digest != expected_digest:
                #           raise ValueError("checksum mismatch")
                checksum = hashlib.sha256(staged.read_bytes()).hexdigest()
                if checksum != exported["sha256"]:
                    raise ValueError("checksum mismatch")

                # [문제 5 · 한 단어] 검사 완료 파일을 최종 경로로 옮기는 Path 메서드다.
                staged.rename(path)

            result = {"path": str(path), "rows": len(rows), "unique_events": len(set(ids)),
                      "sha256": checksum, "schema_version": "ad-event/v1",
                      "source_kind": "ad-events", "since": exported["since"], "until": exported["until"],
                      "preview": rows[:1]}
        except (OSError, ValueError, KeyError, TypeError, PyMongoError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False))
