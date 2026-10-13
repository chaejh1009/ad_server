import hashlib
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pymongo.errors import PyMongoError

from ads.context_projection import apply_context, context_subject_key, get_context
from ads.mongo import get_db


class Command(BaseCommand):
    help = "별도 학습 대상에서 반영·반복·오래된 상태·충돌·삭제 표시를 관찰합니다."

    def add_arguments(self, parser):
        parser.add_argument("--subject", required=True)

    def handle(self, *args, **options):
        try:
            media_id = settings.ADS_MEDIA_ID
            subject = options["subject"]
            key = context_subject_key(media_id, subject)
            if not subject.startswith("fixture-") or subject == "fixture-":
                raise ValueError("fixture-로 시작하는 새 학습 subject를 사용하세요.")
            database = get_db()
            collection = database.player_context
            if collection.find_one({"_id": key}) is not None:
                raise ValueError("존재하지 않는 새 fixture subject를 사용하세요.")

            def change(version, coins, op="upsert"):
                # 실제 게임 시각을 흉내 내지 않는, 고정된 학습용 입력이다.
                instant = "2026-10-13T00:00:00+00:00"
                context = {"player_id": subject, "room_id": "fixture-room",
                           "coins": coins, "version": version, "updated_at": instant}
                row = {"schema_version": "player-context-change/v1", "source_kind": "teaching-fixture",
                       "media_id": media_id, "subject_id": subject, "op": op,
                       "version": version, "event_time": instant,
                       "context": {} if op == "delete" else context}
                canonical = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                row["change_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                return row

            observations = []

            def observe(label, row, expect_conflict=False):
                before = collection.find_one({"_id": key})
                try:
                    status = apply_context(row)
                except ValueError as error:
                    if not expect_conflict or not str(error).startswith("version_conflict:"):
                        raise
                    status = "version_conflict"
                else:
                    if expect_conflict:
                        raise ValueError("동일 version의 다른 상태가 거절되지 않았습니다.")
                after = collection.find_one({"_id": key})
                observations.append({"step": label, "status": status,
                                     "incoming_version": row["version"],
                                     "stored_version": after["version"],
                                     "stored_coins": after["context"].get("coins"),
                                     "deleted": after["deleted"], "unchanged": before == after})

            newest = change(2, 4)
            observe("first", change(1, 3))
            observe("newer", newest)
            observe("repeat", newest)
            observe("older", change(1, 3))
            # 바뀐 내용으로 ID도 다시 계산해 version 충돌만 검증한다.
            observe("conflict", change(2, 99), expect_conflict=True)
            observe("delete", change(3, 0, "delete"))
            observe("older-after-delete", newest)
            result = {"database": database.name, "key": key, "steps": observations,
                      "stored_document": collection.find_one({"_id": key}),
                      "visible_context": get_context(media_id, subject)}
        except (OSError, ValueError, TypeError, KeyError, PyMongoError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=False))