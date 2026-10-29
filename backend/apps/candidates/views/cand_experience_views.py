from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.accounts.models import CandidateProfile
from apps.candidates.models import CandExperience
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# CREATE EXPERIENCE
# POST /api/experiences/create/
# Body: { candidate_id, company_name, designation, start_date, end_date? }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def experience_create(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["candidate_id", "company_name", "designation", "start_date"])
    if err:
        return error_response(err, status=400)

    try:
        candidate = CandidateProfile.objects.get(pk=data["candidate_id"])
    except CandidateProfile.DoesNotExist:
        return error_response("Candidate profile not found", status=404)

    exp = CandExperience.objects.create(
        candidate=candidate,
        company_name=data["company_name"],
        designation=data["designation"],
        start_date=data["start_date"],
        end_date=data.get("end_date"),
    )

    return success_response(
        {
            "exp_id": exp.exp_id,
            "candidate_id": exp.candidate.candidate_id,
            "company_name": exp.company_name,
            "designation": exp.designation,
            "start_date": exp.start_date,
            "end_date": exp.end_date,
        },
        message="Experience created",
        status=201,
    )


# ============================================================
# LIST EXPERIENCES
# GET /api/experiences/
# ============================================================
@require_http_methods(["GET"])
def experience_list(request):
    items = list(
        CandExperience.objects.values(
            "exp_id", "candidate_id", "company_name",
            "designation", "start_date", "end_date",
        )
    )
    return success_response(items, message="Experiences fetched")


# ============================================================
# GET ONE EXPERIENCE
# GET /api/experiences/<exp_id>/
# ============================================================
@require_http_methods(["GET"])
def experience_detail(request, exp_id):
    try:
        exp = CandExperience.objects.select_related("candidate").get(pk=exp_id)
    except CandExperience.DoesNotExist:
        return error_response("Experience not found", status=404)

    return success_response({
        "exp_id": exp.exp_id,
        "candidate_id": exp.candidate.candidate_id,
        "full_name": exp.candidate.user.full_name,
        "email": exp.candidate.user.email,
        "company_name": exp.company_name,
        "designation": exp.designation,
        "start_date": exp.start_date,
        "end_date": exp.end_date,
    }, message="Experience fetched")


# ============================================================
# UPDATE EXPERIENCE
# PUT /api/experiences/<exp_id>/update/
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def experience_update(request, exp_id):
    try:
        exp = CandExperience.objects.get(pk=exp_id)
    except CandExperience.DoesNotExist:
        return error_response("Experience not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "company_name" in data:
        exp.company_name = data["company_name"]
    if "designation" in data:
        exp.designation = data["designation"]
    if "start_date" in data:
        exp.start_date = data["start_date"]
    if "end_date" in data:
        exp.end_date = data["end_date"]

    exp.save()
    return success_response(
        {"exp_id": exp.exp_id},
        message="Experience updated",
    )


# ============================================================
# DELETE EXPERIENCE
# DELETE /api/experiences/<exp_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def experience_delete(request, exp_id):
    try:
        exp = CandExperience.objects.get(pk=exp_id)
    except CandExperience.DoesNotExist:
        return error_response("Experience not found", status=404)

    exp.delete()
    return success_response(message="Experience deleted")