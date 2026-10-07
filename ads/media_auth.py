import hmac
import json
from functools import wraps
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pymongo.errors import PyMongoError
from .services import clean_subject


# 서버 간 인증을 먼저 검사한 뒤 subject와 JSON 데이터를 뷰에 전달한다.
def media_api_methods(*allowed):
    def decorate(view):
        @csrf_exempt
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method not in allowed:
                response = JsonResponse({"error": "method_not_allowed"}, status=405)
                response["Allow"] = ", ".join(allowed)
                return response
            media_id = request.headers.get("X-Media-ID", "")
            expected = settings.MEDIA_KEYS.get(media_id)
            provided = request.headers.get("X-Media-Key", "")
            if not expected or not hmac.compare_digest(expected, provided):
                return JsonResponse({"error": "media_auth_required"}, status=401)
            try:
                if request.content_type != "application/json":
                    raise ValueError("application/json is required")
                body = json.loads(request.body)
                if not isinstance(body, dict):
                    raise ValueError("JSON object is required")
                request.subject = clean_subject(body.get("subject"))
                if request.subject["media_id"] != media_id:
                    raise ValueError("media_id does not match authenticated media")
                request.media_body = body
                return view(request, *args, **kwargs)
            except (ValueError, UnicodeDecodeError) as exc:
                return JsonResponse({"error": str(exc)}, status=400)
            except PyMongoError:
                return JsonResponse({"error": "ads_unavailable"}, status=503)
        return wrapped
    return decorate