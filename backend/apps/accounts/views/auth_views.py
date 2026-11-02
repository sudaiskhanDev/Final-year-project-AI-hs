from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.accounts.models import User, CandidateProfile, HRProfile
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields
  
# ============================================================
# HELPER — role-specific ID bhi payload mein add karta hai
# ============================================================
def build_user_payload(user):
    data = {
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "phone_no": user.phone_no,
        "role": user.role,
    }
    if user.role == "candidate":
        profile, _ = CandidateProfile.objects.get_or_create(user=user)
        data["candidate_id"] = profile.candidate_id
    elif user.role == "hr":
        profile, _ = HRProfile.objects.get_or_create(user=user)
        data["hr_id"] = profile.hr_id
    return data


# ============================================================
# REGISTER
# POST /api/auth/register/
# Body: { full_name, email, password, confirm_password, phone_no?, role? }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    # Required fields
    err = require_fields(data, ["full_name", "email", "password", "confirm_password"])
    if err:
        return error_response(err, status=400)

    # Password match
    if data["password"] != data["confirm_password"]:
        return error_response("Passwords do not match", status=400)

    # Password length (basic)
    if len(data["password"]) < 8:
        return error_response("Password must be at least 8 characters", status=400)

    # Email unique
    if User.objects.filter(email=data["email"]).exists():
        return error_response("Email already registered", status=409)

    # Role validate — register pe sirf 'candidate' ya 'hr' allow karenge
    # 'admin' sirf superuser/admin dashboard se banega
    role = data.get("role", "candidate")
    allowed_roles = ["candidate", "hr"]
    if role not in allowed_roles:
        return error_response(f"Invalid role. Allowed at register: {allowed_roles}", status=400)

    user = User.objects.create(
        full_name=data["full_name"],
        email=data["email"],
        phone_no=data.get("phone_no", ""),
        role=role,
        password=make_password(data["password"]),
    )

    return success_response(
        {
            "user_id": user.user_id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
        },
        message="Registration successful",
        status=201,
    )


# ============================================================
# LOGIN
# POST /api/auth/login/
# Body: { email, password }
# Session cookie set hoti hai response mein
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["email", "password"])
    if err:
        return error_response(err, status=400)

    # authenticate() email + password check karta hai (USERNAME_FIELD = email)
    user = authenticate(request, username=data["email"], password=data["password"])
    if user is None:
        return error_response("Invalid email or password", status=401)

    if not user.is_active:
        return error_response("Account is inactive", status=403)

    # Django session create karo (cookie automatically set hoti hai)
    django_login(request, user)

    return success_response(
        build_user_payload(user),
        # {
        #     "user_id": user.user_id,
        #     "full_name": user.full_name,
        #     "email": user.email,
        #     "role": user.role,
        # },
        message="Login successful",
    )


# ============================================================
# LOGOUT
# POST /api/auth/logout/
# Session destroy karta hai
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def logout(request):
    if not request.user.is_authenticated:
        return error_response("Not logged in", status=401)

    django_logout(request)
    return success_response(message="Logout successful")


# ============================================================
# ME — current logged-in user
# GET /api/auth/me/
# ============================================================
@require_http_methods(["GET"])
def me(request):
    if not request.user.is_authenticated:
        return error_response("Not authenticated", status=401)

    user = request.user
    payload = build_user_payload(user)
    payload["is_active"] = user.is_active
    payload["created_at"] = user.created_at
    return success_response(payload, message="Current user")


    # user = request.user
    # return success_response(
    #     {
    #     "user_id": user.user_id,
    #     "full_name": user.full_name,
    #     "email": user.email,
    #     "phone_no": user.phone_no,
    #     "role": user.role,
    #     "is_active": user.is_active,
    #     "created_at": user.created_at,
    # }, message="Current user") z