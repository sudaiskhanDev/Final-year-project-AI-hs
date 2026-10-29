from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.accounts.models import CandidateProfile
from apps.candidates.models import CandidateQualification
from apps.masterdata.models import Qualification
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# CREATE CANDIDATE QUALIFICATION
# POST /api/candidate-qualifications/create/
# Body: { candidate_id, qualification_id }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def cand_qualification_create(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["candidate_id", "qualification_id"])
    if err:
        return error_response(err, status=400)

    try:
        candidate = CandidateProfile.objects.get(pk=data["candidate_id"])
    except CandidateProfile.DoesNotExist:
        return error_response("Candidate profile not found", status=404)

    try:
        qualification = Qualification.objects.get(pk=data["qualification_id"])
    except Qualification.DoesNotExist:
        return error_response("Qualification not found", status=404)

    if CandidateQualification.objects.filter(candidate=candidate, qualification=qualification).exists():
        return error_response("This candidate already has this qualification", status=409)

    cq = CandidateQualification.objects.create(
        candidate=candidate,
        qualification=qualification,
    )

    return success_response(
        {
            "cq_id": cq.cq_id,
            "candidate_id": cq.candidate.candidate_id,
            "qualification_id": cq.qualification.qualification_id,
            "qualification_name": cq.qualification.qualification_name,
        },
        message="Candidate qualification created",
        status=201,
    )


# ============================================================
# LIST CANDIDATE QUALIFICATIONS
# GET /api/candidate-qualifications/
# ============================================================
@require_http_methods(["GET"])
def cand_qualification_list(request):
    items = list(
        CandidateQualification.objects.select_related("candidate", "qualification").values(
            "cq_id",
            "candidate_id",
            "qualification_id",
            "qualification__qualification_name",
        )
    )
    result = [
        {
            "cq_id": item["cq_id"],
            "candidate_id": item["candidate_id"],
            "qualification_id": item["qualification_id"],
            "qualification_name": item["qualification__qualification_name"],
        }
        for item in items
    ]
    return success_response(result, message="Candidate qualifications fetched")


# ============================================================
# GET ONE CANDIDATE QUALIFICATION
# GET /api/candidate-qualifications/<cq_id>/
# ============================================================
@require_http_methods(["GET"])
def cand_qualification_detail(request, cq_id):
    try:
        cq = CandidateQualification.objects.select_related("candidate", "qualification").get(pk=cq_id)
    except CandidateQualification.DoesNotExist:
        return error_response("Candidate qualification not found", status=404)

    return success_response({
        "cq_id": cq.cq_id,
        "candidate_id": cq.candidate.candidate_id,
        "full_name": cq.candidate.user.full_name,
        "qualification_id": cq.qualification.qualification_id,
        "qualification_name": cq.qualification.qualification_name,
    }, message="Candidate qualification fetched")


# ============================================================
# UPDATE CANDIDATE QUALIFICATION — change qualification
# PUT /api/candidate-qualifications/<cq_id>/update/
# Body: { qualification_id }
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def cand_qualification_update(request, cq_id):
    try:
        cq = CandidateQualification.objects.get(pk=cq_id)
    except CandidateQualification.DoesNotExist:
        return error_response("Candidate qualification not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "qualification_id" in data:
        try:
            new_qual = Qualification.objects.get(pk=data["qualification_id"])
        except Qualification.DoesNotExist:
            return error_response("Qualification not found", status=404)

        if CandidateQualification.objects.filter(candidate=cq.candidate, qualification=new_qual).exclude(pk=cq_id).exists():
            return error_response("This candidate already has this qualification", status=409)

        cq.qualification = new_qual
        cq.save()

    return success_response(
        {"cq_id": cq.cq_id},
        message="Candidate qualification updated",
    )


# ============================================================
# DELETE CANDIDATE QUALIFICATION
# DELETE /api/candidate-qualifications/<cq_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def cand_qualification_delete(request, cq_id):
    try:
        cq = CandidateQualification.objects.get(pk=cq_id)
    except CandidateQualification.DoesNotExist:
        return error_response("Candidate qualification not found", status=404)

    cq.delete()
    return success_response(message="Candidate qualification deleted")