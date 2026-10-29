from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.accounts.models import User, HRProfile
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields
# from utils.decorators import admin_required_json, login_required_json   # ← testing ke liye comment


# ============================================================
# CREATE HR PROFILE
# POST /api/hr-profiles/create/
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def hr_profile_create(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["user_id", "department", "designation"])
    if err:
        return error_response(err, status=400)

    try:
        user = User.objects.get(pk=data["user_id"])
    except User.DoesNotExist:
        return error_response("User not found", status=404)

    if user.role != "hr":
        return error_response(
            f"User role must be 'hr' to create HR profile (current: {user.role})",
            status=400,
        )

    if HRProfile.objects.filter(user=user).exists():
        return error_response("HR profile already exists for this user", status=409)

    profile = HRProfile.objects.create(
        user=user,
        department=data["department"],
        designation=data["designation"],
    )

    return success_response(
        {
            "hr_id": profile.hr_id,
            "user_id": profile.user.user_id,
            "department": profile.department,
            "designation": profile.designation,
        },
        message="HR profile created",
        status=201,
    )


# ============================================================
# LIST HR PROFILES
# GET /api/hr-profiles/
# ============================================================
@require_http_methods(["GET"])
def hr_profile_list(request):
    profiles = list(
        HRProfile.objects.values(
            "hr_id", "user_id", "department", "designation", "created_at",
        )
    )
    return success_response(profiles, message="HR profiles fetched")


# ============================================================
# GET ONE HR PROFILE
# GET /api/hr-profiles/<hr_id>/
# ============================================================
@require_http_methods(["GET"])
def hr_profile_detail(request, hr_id):
    try:
        profile = HRProfile.objects.select_related("user").get(pk=hr_id)
    except HRProfile.DoesNotExist:
        return error_response("HR profile not found", status=404)

    return success_response({
        "hr_id": profile.hr_id,
        "user_id": profile.user.user_id,
        "full_name": profile.user.full_name,
        "email": profile.user.email,
        "department": profile.department,
        "designation": profile.designation,
        "created_at": profile.created_at,
    }, message="HR profile fetched")


# ============================================================
# UPDATE HR PROFILE
# PUT /api/hr-profiles/<hr_id>/update/
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def hr_profile_update(request, hr_id):
    try:
        profile = HRProfile.objects.get(pk=hr_id)
    except HRProfile.DoesNotExist:
        return error_response("HR profile not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "department" in data:
        profile.department = data["department"]
    if "designation" in data:
        profile.designation = data["designation"]

    profile.save()
    return success_response(
        {"hr_id": profile.hr_id},
        message="HR profile updated",
    )


# ============================================================
# DELETE HR PROFILE
# DELETE /api/hr-profiles/<hr_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def hr_profile_delete(request, hr_id):
    try:
        profile = HRProfile.objects.get(pk=hr_id)
    except HRProfile.DoesNotExist:
        return error_response("HR profile not found", status=404)

    profile.delete()
    return success_response(message="HR profile deleted")