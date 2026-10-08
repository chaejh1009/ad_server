import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from ads.exporting import read_ndjson
from ads.mongo import get_db
from ads.reporting import build_daily_reports


class Command(BaseCommand):
    help = "전체 보관 사건의 고정 입력과 게시 보고서를 대조합니다."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        source = Path(options["source"])
        events = read_ndjson(source)
        expected = {row["_id"]: row for row in build_daily_reports(events)}
        actual = {row["_id"]: row for row in get_db().ad_daily_reports.find()}
        fields = ("impressions", "clicks", "ctr", "bid_units_sum", "source_max_event_time")
        # [문제 1 · 여러 줄] 기대에만 있는 키와 게시에만 있는 키를 정렬해 각각 보관한다. (2줄)
        # 예시: absent = sorted(planned.keys() - received.keys())
        #       unexpected = sorted(received.keys() - planned.keys())
        missing = sorted(expected.keys() - actual.keys())
        extra = sorted(actual.keys() - expected.keys())


        # [문제 2 · 여러 줄] 공통 키 중 fields의 값 하나라도 다른 키를 정렬한다. (2줄)
        # 예시: changed = sorted(name for name in before.keys() & after.keys()
        #                        if any(before[name][part] != after[name][part] for part in parts))
        different = sorted(key for key in expected.keys() & actual.keys()
               if any(expected[key][field] != actual[key][field] for field in fields))
        # [문제 3 · 한 단어] 세 목록이 모두 비어 있을 때만 True가 되는 논리 부정 연산자다.
        result = {
            "artifact_id": "village-lab.ads-analytics", "artifact_version": "v2",
            "source_kind": "ad-events", "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "source_rows": len(events), "unique_events": len({row["event_id"] for row in events}),
            "missing_report_keys": missing, "extra_report_keys": extra,
            "different_report_keys": different, "ok": not(missing or extra or different),
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "transport": "file", "spark_ad_job_status": "not-configured",
            "gui_status": "separate-manual-observation",
        }
        # [문제 4 · 여러 줄] 출력 경로·상위 폴더를 만들고 결과 JSON과 마지막 줄바꿈을 저장한다. (3줄)
        # 예시: log = Path(arguments["log"])
        #       log.parent.mkdir(parents=True, exist_ok=True)
        #       log.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        log = Path(options["output"])
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        self.stdout.write(json.dumps(result, ensure_ascii=False))
        if not result["ok"]:
            # [문제 5 · 한 줄] 이미 증거를 저장한 뒤 실패 종료를 알린다.
            # 예시: raise CommandError("검사 결과를 확인하세요.")
            raise CommandError("보고서 누락, 혹은 추가나 차이 발생")
