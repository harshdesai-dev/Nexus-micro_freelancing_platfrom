import json
from functools import wraps

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from accounts.serializers import user_to_dict


def body(request):
    """Safely parse JSON request body."""
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


def success(data=None, message="", status=200):
    """Standard NEXUS success response envelope."""
    payload = {"success": True, "data": data if data is not None else {}}
    if message:
        payload["message"] = message
    return JsonResponse(payload, status=status)


def error(code, message, status=400):
    """Standard NEXUS error response envelope."""
    return JsonResponse(
        {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
        status=status,
    )


def jwt_required(view_func):
    """Decorator to authenticate requests via SimpleJWT."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        authenticator = JWTAuthentication()
        try:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header:
                return error("UNAUTHORIZED", "Authentication credentials were not provided.", 401)
            raw_token = authenticator.get_raw_token(authenticator.get_header(request))
            if raw_token is None:
                return error("UNAUTHORIZED", "Authentication credentials were not provided.", 401)
            validated_token = authenticator.get_validated_token(raw_token)
            request.user = authenticator.get_user(validated_token)
            if not request.user.is_authenticated or request.user.account_status != User.AccountStatus.ACTIVE:
                return error("UNAUTHORIZED", "User account is not active.", 401)
        except Exception:
            return error("UNAUTHORIZED", "Invalid or expired authentication token.", 401)
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    """Decorator to enforce specific user roles."""
    def decorator(view_func):
        @jwt_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                return error("FORBIDDEN", "You do not have permission to perform this action.", 403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


@csrf_exempt
@require_http_methods(["POST"])
def register_view(request):
    data = body(request)
    if data is None:
        return error("INVALID_JSON", "Invalid JSON in request body.")
    required_fields = ["username", "email", "password"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return error("VALIDATION_ERROR", "Missing required fields: " + ", ".join(missing) + ".")
    role = str(data.get("role", User.Role.STUDENT)).upper()
    if role not in User.Role.values:
        return error("VALIDATION_ERROR", f"Invalid role: {role}. Must be STUDENT or CLIENT.")
    if User.objects.filter(username=data["username"]).exists():
        return error("USERNAME_EXISTS", "A user with this username already exists.", 409)
    if User.objects.filter(email=data["email"]).exists():
        return error("EMAIL_EXISTS", "A user with this email already exists.", 409)
    user = User.objects.create_user(
        username=data["username"],
        email=data["email"],
        password=data["password"],
        role=role,
        name=data.get("name", ""),
    )
    refresh = RefreshToken.for_user(user)
    return success(
        {
            "user": user_to_dict(user),
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
        },
        "User registered successfully",
        201,
    )


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    data = body(request)
    if data is None:
        return error("INVALID_JSON", "Invalid JSON in request body.")
    username = data.get("username") or data.get("email")
    password = data.get("password")
    if not username or not password:
        return error("VALIDATION_ERROR", "Username and password are required.")
    user = None
    if "@" in username:
        user_obj = User.objects.filter(email=username).first()
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
    else:
        user = authenticate(request, username=username, password=password)
    if not user:
        return error("INVALID_CREDENTIALS", "Invalid username or password.", 401)
    if user.account_status != User.AccountStatus.ACTIVE:
        return error("ACCOUNT_DISABLED", "Your account has been suspended or disabled.", 403)
    refresh = RefreshToken.for_user(user)
    return success(
        {
            "user": user_to_dict(user),
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
        },
        "Login successful",
    )


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def logout_view(request):
    data = body(request)
    if data and data.get("refresh"):
        try:
            token = RefreshToken(data["refresh"])
            token.blacklist()
        except Exception:
            pass
    return success({}, "Logged out successfully")


@csrf_exempt
@require_http_methods(["GET", "PATCH"])
@jwt_required
def me_view(request):
    if request.method == "PATCH":
        data = body(request)
        if data is None:
            return error("INVALID_JSON", "Invalid JSON in request body.")
        if "name" in data:
            request.user.name = data["name"]
        if "email" in data:
            request.user.email = data["email"]
        request.user.save(update_fields=["name", "email", "updated_at"])
    return success({"user": user_to_dict(request.user)})
