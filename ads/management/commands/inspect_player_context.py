import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pymongo.errors import PyMongoError

from ads.context_projection import context_subject_key, make_context_document
from ads.exporting import read_ndjson
from ads.mongo import get_db


class Command(BaseCommand):
    help = "정규화 문서를 미리보고 고유 인덱스와 현재 저장 상태를 확인합니다."

    def add_arguments(self, parser):
        parser.add_argument("--source")
        parser.add_argument("--media-id", default=settings.ADS_MEDIA_ID)
        parser.add_argument("--subject")

    def handle(self, *args, **options):
        try:
            media_id, subject = options["media_id"], options["subject"]
            context_subject_key(media_id, subject if subject is not None else "inspect")
            documents = None
            if options["source"]:
                documents = [make_context_document(row) for row in read_ndjson(options["source"])]
                if any(document["media_id"] != media_id for document in documents):
                    raise ValueError("입력 media_id와 --media-id가 다릅니다.")
            db = get_db()
            collection = db.player_context
            name = collection.create_index([("media_id", 1), ("subject_id", 1)],
                                           unique=True, name="media_subject_once")
            query = {"media_id": media_id}
            if subject is not None:
                query["_id"] = context_subject_key(media_id, subject)
            rows = list(collection.find(query).sort("_id", 1))
            result = {"database": db.name, "count": len(rows),
                      "index": collection.index_information()[name], "rows": rows,
                      "input_rows": None if documents is None else len(documents),
                      "document_preview": [] if documents is None else documents[:1]}
        except (OSError, TypeError, ValueError, KeyError, PyMongoError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))