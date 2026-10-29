from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.accounts.models import User, CandidateProfile
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields
# from utils.decorators import admin_required_json   # testing ke liye comment


# ============================================================
# CREATE CANDIDATE PROFILE
# POST /api/candidate-profiles/create/
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def candidate_profile_create(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["user_id"])
    if err:
        return error_response(err, status=400)

    try:
        user = User.objects.get(pk=data["user_id"])
    except User.DoesNotExist:
        return error_response("User not found", status=404)

    if user.role != "candidate":
        return error_response(
            f"User role must be 'candidate' (current: {user.role})",
            status=400,
        )

    if CandidateProfile.objects.filter(user=user).exists():
        return error_response("Candidate profile already exists for this user", status=409)

    gender = data.get("gender")
    if gender:
        valid_genders = [g[0] for g in CandidateProfile.GENDER_CHOICES]
        if gender not in valid_genders:
            return error_response(f"Invalid gender. Allowed: {valid_genders}", status=400)

    profile = CandidateProfile.objects.create(
        user=user,
        date_of_birth=data.get("date_of_birth"),
        gender=gender,
        address=data.get("address"),
    )

    return success_response(
        {
            "candidate_id": profile.candidate_id,
            "user_id": profile.user.user_id,
            "date_of_birth": profile.date_of_birth,
            "gender": profile.gender,
            "address": profile.address,
        },
        message="Candidate profile created",
        status=201,
    )


# ============================================================
# LIST CANDIDATE PROFILES
# GET /api/candidate-profiles/
# ============================================================
@require_http_methods(["GET"])
def candidate_profile_list(request):
    profiles = list(
        CandidateProfile.objects.values(
            "candidate_id", "user_id", "date_of_birth",
            "gender", "address", "created_at",
        )
    )
    return success_response(profiles, message="Candidate profiles fetched")


# ============================================================
# GET ONE CANDIDATE PROFILE
# GET /api/candidate-profiles/<candidate_id>/
# ============================================================
@require_http_methods(["GET"])
def candidate_profile_detail(request, candidate_id):
    try:
        profile = CandidateProfile.objects.select_related("user").get(pk=candidate_id)
    except CandidateProfile.DoesNotExist:
        return error_response("Candidate profile not found", status=404)

    return success_response({
        "candidate_id": profile.candidate_id,
        "user_id": profile.user.user_id,
        "full_name": profile.user.full_name,
        "email": profile.user.email,
        "phone_no": profile.user.phone_no,
        "date_of_birth": profile.date_of_birth,
        "gender": profile.gender,
        "address": profile.address,
        "created_at": profile.created_at,
    }, message="Candidate profile fetched")


# ============================================================
# UPDATE CANDIDATE PROFILE
# PUT /api/candidate-profiles/<candidate_id>/update/
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def candidate_profile_update(request, candidate_id):
    try:
        profile = CandidateProfile.objects.get(pk=candidate_id)
    except CandidateProfile.DoesNotExist:
        return error_response("Candidate profile not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "date_of_birth" in data:
        profile.date_of_birth = data["date_of_birth"]

    if "gender" in data:
        valid_genders = [g[0] for g in CandidateProfile.GENDER_CHOICES]
        if data["gender"] and data["gender"] not in valid_genders:
            return error_response(f"Invalid gender. Allowed: {valid_genders}", status=400)
        profile.gender = data["gender"]

    if "address" in data:
        profile.address = data["address"]

    profile.save()
    return success_response(
        {"candidate_id": profile.candidate_id},
        message="Candidate profile updated",
    )


# ============================================================
# DELETE CANDIDATE PROFILE
# DELETE /api/candidate-profiles/<candidate_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def candidate_profile_delete(request, candidate_id):
    try:
        profile = CandidateProfile.objects.get(pk=candidate_id)
    except CandidateProfile.DoesNotExist:
        return error_response("Candidate profile not found", status=404)

    profile.delete()
    return success_response(message="Candidate profile deleted")