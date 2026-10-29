from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password

from apps.accounts.models import User
from utils.response import success_response, error_response
from utils.validators import parse_json


# ============================================================
# LIST ALL USERS
# GET /api/users/
# ============================================================
@require_http_methods(["GET"])
def user_list(request):
    users = list(
        User.objects.values(
            "user_id", "full_name", "email", "phone_no",
            "role", "is_active", "created_at",
        )
    )
    return success_response(users, message="Users fetched")


# ============================================================
# GET ONE USER
# GET /api/users/<user_id>/
# ============================================================
@require_http_methods(["GET"])
def user_detail(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return error_response("User not found", status=404)

    return success_response({
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "phone_no": user.phone_no,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }, message="User fetched")


# ============================================================
# UPDATE USER
# PUT /api/users/<user_id>/
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def user_update(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return error_response("User not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    # Email uniqueness (agar change ho raha ho)
    new_email = data.get("email")
    if new_email and new_email != user.email:
        if User.objects.filter(email=new_email).exists():
            return error_response("Email already in use", status=409)
        user.email = new_email

    if "full_name" in data:
        user.full_name = data["full_name"]
    if "phone_no" in data:
        user.phone_no = data["phone_no"]

    if "role" in data:
        valid_roles = [r[0] for r in User.ROLE_CHOICES]
        if data["role"] not in valid_roles:
            return error_response(f"Invalid role. Allowed: {valid_roles}", status=400)
        user.role = data["role"]

    if "password" in data and data["password"]:
        user.password = make_password(data["password"])

    user.save()
    return success_response({"user_id": user.user_id}, message="User updated")


# ============================================================
# DELETE USER
# DELETE /api/users/<user_id>/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def user_delete(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return error_response("User not found", status=404)

    user.delete()
    return success_response(message="User deleted")