import json
from django.core.management.base import BaseCommand
from ads.mongo import get_db


class Command(BaseCommand):
    def handle(self, *args, **options):
        collection = get_db().player_context
        collection.create_index([("media_id", 1), ("subject_id", 1)],
                                unique=True, name="media_subject_once")
        rows = list(collection.find({}, {"_id": 1, "media_id": 1, "subject_id": 1,
                                         "version": 1, "deleted": 1, "source_kind": 1}))
        self.stdout.write(json.dumps({"count": len(rows), "rows": rows}, ensure_ascii=False))