import json
from functools import wraps

from django.http import JsonResponse
from pymongo.errors import PyMongoError
from .media_auth import media_api_methods
from . import services


# 로그인·허용 HTTP 메서드를 검사하고 입력 오류는 400, 저장소 오류는 503으로 응답한다.
def api_methods(*allowed):
    def decorate(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({"error": "login_required"}, status=401)
            if request.method not in allowed:
                response = JsonResponse({"error": "method_not_allowed"}, status=405)
                response["Allow"] = ", ".join(allowed)
                return response
            try:
                return view(request, *args, **kwargs)
            except ValueError as exc:
                return JsonResponse({"error": str(exc)}, status=400)
            except PyMongoError:
                return JsonResponse({"error": "ads_unavailable"}, status=503)
        return wrapped
    return decorate


# application/json 본문을 해석해 JSON 객체만 입력으로 받는다.
def read_json(request):
    if request.content_type != "application/json":
        raise ValueError("application/json is required")
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("invalid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("JSON object is required")
    return data


# GET은 사용자 캠페인 목록을, POST는 검증 후 저장한 캠페인을 반환한다.
@api_methods("GET", "POST")
def campaigns(request):
    if request.method == "GET":
        return JsonResponse({"rows": services.list_campaigns(request.user)})
    return JsonResponse(
        services.save_campaign(request.user, read_json(request)),
        status=200,
    )

# GET은 사용자 입찰 목록을, POST는 검증 후 저장한 입찰을 반환한다.
@api_methods("GET", "POST")
def bids(request):
    if request.method == "GET":
        return JsonResponse({"rows": services.list_bids(request.user)})
    return JsonResponse(
        services.save_bid(request.user, read_json(request)),
        status=200,
    )

# 광고 서버는 게임 객체 대신 인증된 매체 subject와 공개 context를 받는다.
@media_api_methods("POST")
def decision(request):
    result = services.choose_ad(
        request.subject,
        request.media_body.get("slot_id"),
        request.media_body.get("context"),
    )
    response = JsonResponse(result)
    response["Cache-Control"] = "no-store"
    return response