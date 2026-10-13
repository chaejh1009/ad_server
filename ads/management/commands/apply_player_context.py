import json

from django.core.management.base import BaseCommand, CommandError
from pymongo.errors import PyMongoError

from ads.context_projection import apply_context, make_context_document, get_context
from ads.exporting import read_ndjson
from ads.mongo import get_db


class Command(BaseCommand):
    help = "정규화 파일의 지정 행을 최신 공개 context에 반영합니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--row", type=int, default=1)

    def handle(self, *args, **options):
        try:
            rows = read_ndjson(options["source"])
            documents = [make_context_document(row) for row in rows]
            number = options["row"]
            if not documents:
                raise ValueError("입력이 0행입니다. 반영할 대상이 없습니다.")
            if not 1 <= number <= len(documents):
                raise ValueError("--row는 1부터 입력 행 수 사이여야 합니다.")
            document = documents[number - 1]
            status = apply_context(rows[number - 1])
            database = get_db()
            stored = database.player_context.find_one({"_id": document["_id"]})
            result = {"database": database.name, "source": options["source"],
                      "row": number, "input_rows": len(rows), "status": status,
                      "key": document["_id"], "incoming_version": document["version"],
                      "stored_version": stored["version"], "stored_document": stored,
                      "context": get_context(document["media_id"], document["subject_id"])}
        except (OSError, ValueError, TypeError, KeyError, PyMongoError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False))