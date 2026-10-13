import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pymongo.errors import PyMongoError

from ads.context_projection import context_subject_key, get_context
from ads.mongo import get_db


class Command(BaseCommand):
    help = "선택 당시 context와 현재 공개 복사본을 읽기만 하여 비교합니다."

    def add_arguments(self, parser):
        choice = parser.add_mutually_exclusive_group(required=True)
        choice.add_argument("--decision-id")
        choice.add_argument("--subject")
        parser.add_argument("--latest", action="store_true")
        parser.add_argument("--media-id", default=settings.ADS_MEDIA_ID)

    def handle(self, *args, **options):
        try:
            media_id = options["media_id"]
            context_subject_key(media_id, options["subject"] or "inspection")
            query = {"subject.media_id": media_id}
            if options["decision_id"] is not None:
                if options["latest"]:
                    raise ValueError("--decision-id와 --latest를 함께 지정하지 않습니다.")
                if not options["decision_id"].strip():
                    raise ValueError("decision_id는 비어 있지 않아야 합니다.")
                query["_id"] = options["decision_id"]
            else:
                if not options["latest"]:
                    raise ValueError("--subject 조회에는 --latest를 함께 지정하세요.")
                query["subject.subject_id"] = options["subject"]
            projection = {"_id": 1, "subject": 1, "context": 1, "selected_at": 1}
            row = get_db().decisions.find_one(query, projection,
                                              sort=[("selected_at", -1), ("_id", -1)])
            if row is None:
                raise ValueError("선택 기록이 없습니다. empty 응답은 decision을 저장하지 않습니다.")
            subject = row["subject"]
            saved = dict(row["context"])
            current = get_context(subject["media_id"], subject["subject_id"])
            names = sorted(set(saved) | set(current))
            differences = {name: {"decision": saved.get(name), "current": current.get(name)}
                           for name in names if saved.get(name) != current.get(name)
                           or (name in saved) != (name in current)}
            instant = row.get("selected_at")
            result = {"decision_id": row["_id"], "subject": subject,
                      "selected_at": instant.isoformat() if hasattr(instant, "isoformat") else instant,
                      "context": saved, "current_context": current,
                      "same_context": saved == current, "differences": differences}
        except (ValueError, TypeError, KeyError, PyMongoError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))