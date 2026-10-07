"""Advertiser web forms using the currently implemented advertising services."""
import re

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from pymongo.errors import PyMongoError

from . import services


@login_required(login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def campaign_view(request):
    message, status, campaigns = "", 200, []
    try:
        if request.method == "POST":
            services.save_campaign(request.user, {
                "campaign_id": request.POST.get("campaign_id", ""),
                "title": request.POST.get("title", ""),
                "creative_path": request.POST.get("creative_path", ""),
                "media_id": "village-game",
                "slot_id": request.POST.get("slot_id", ""),
                "active": request.POST.get("active") == "on",
            })
            message = "캠페인을 저장했습니다."
        campaigns = services.list_campaigns(request.user)
    except ValueError as error:
        message, status = str(error), 400
    except PyMongoError:
        message, status = "광고 저장소에 연결할 수 없습니다.", 503
    return render(request, "ads/campaigns.html",
                  {"campaigns": campaigns, "message": message}, status=status)


@login_required(login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def bid_view(request):
    message, status, bids = "", 200, []
    try:
        if request.method == "POST":
            raw_amount = request.POST.get("bid_amount", "").strip()
            if not re.fullmatch(r"[0-9]{1,5}", raw_amount):
                raise ValueError("입찰 포인트는 1~10000의 정수로 입력하세요.")
            amount = int(raw_amount)
            if not 1 <= amount <= 10000:
                raise ValueError("입찰 포인트는 1~10000의 정수로 입력하세요.")
            services.save_bid(request.user, {
                "campaign_id": request.POST.get("campaign_id", ""),
                "bid_units": amount,
            })
            message = "입찰을 저장했습니다. 다음 광고 선택에 반영됩니다."
        # Keep the current Mongo/API field and adapt only the web projection.
        bids = [{**row, "bid_amount": row["bid_units"]}
                for row in services.list_bids(request.user)]
    except ValueError as error:
        message, status = str(error), 400
    except PyMongoError:
        message, status = "광고 저장소에 연결할 수 없습니다.", 503
    return render(request, "ads/bids.html",
                  {"bids": bids, "message": message}, status=status)
