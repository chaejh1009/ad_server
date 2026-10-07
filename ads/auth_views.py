import json
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST


@require_GET
@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})


@require_POST
def login_view(request):
    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "invalid_json"}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"error": "invalid_json"}, status=400)
    username, password = payload.get("username"), payload.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return JsonResponse({"error": "missing_credentials"}, status=400)
    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"authenticated": False}, status=401)
    login(request, user)
    return JsonResponse({"authenticated": True})


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"authenticated": False})