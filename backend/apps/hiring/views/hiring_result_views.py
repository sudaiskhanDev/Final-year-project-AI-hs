from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.recruitment.models import Application
from apps.hiring.models import HiringResult
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# CREATE HIRING RESULT
# POST /api/hiring-results/create/
# Body: { application_id, final_score?, ranking?, selection_status?, remarks?, decision_date? }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def hiring_result_create(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["application_id"])
    if err:
        return error_response(err, status=400)

    try:
        application = Application.objects.get(pk=data["application_id"])
    except Application.DoesNotExist:
        return error_response("Application not found", status=404)

    if HiringResult.objects.filter(application=application).exists():
        return error_response("Hiring result already exists for this application", status=409)

    status_val = data.get("selection_status", "shortlisted")
    valid = [c[0] for c in HiringResult.SELECTION_CHOICES]
    if status_val not in valid:
        return error_response(f"Invalid selection_status. Allowed: {valid}", status=400)

    hr = HiringResult.objects.create(
        application=application,
        final_score=data.get("final_score", 0),
        ranking=data.get("ranking", 0),
        selection_status=status_val,
        remarks=data.get("remarks"),
        decision_date=data.get("decision_date"),
    )

    return success_response(
        {
            "result_id": hr.result_id,
            "application_id": hr.application.application_id,
            "final_score": str(hr.final_score),
            "ranking": hr.ranking,
            "selection_status": hr.selection_status,
            "remarks": hr.remarks,
            "decision_date": hr.decision_date,
        },
        message="Hiring result created",
        status=201,
    )


# ============================================================
# LIST HIRING RESULTS
# GET /api/hiring-results/
# ============================================================
@require_http_methods(["GET"])
def hiring_result_list(request):
    items = list(
        HiringResult.objects.select_related("application").values(
            "result_id",
            "application_id",
            "final_score",
            "ranking",
            "selection_status",
            "remarks",
            "decision_date",
        )
    )
    for item in items:
        item["final_score"] = str(item["final_score"])
    return success_response(items, message="Hiring results fetched")


# ============================================================
# GET ONE HIRING RESULT
# GET /api/hiring-results/<result_id>/
# ============================================================
@require_http_methods(["GET"])
def hiring_result_detail(request, result_id):
    try:
        hr = HiringResult.objects.select_related(
            "application__candidate__user",
            "application__job",
        ).get(pk=result_id)
    except HiringResult.DoesNotExist:
        return error_response("Hiring result not found", status=404)

    return success_response({
        "result_id": hr.result_id,
        "application_id": hr.application.application_id,
        "candidate_id": hr.application.candidate.candidate_id,
        "candidate_name": hr.application.candidate.user.full_name,
        "candidate_email": hr.application.candidate.user.email,
        "job_id": hr.application.job.job_id,
        "job_title": hr.application.job.job_title,
        "final_score": str(hr.final_score),
        "ranking": hr.ranking,
        "selection_status": hr.selection_status,
        "remarks": hr.remarks,
        "decision_date": hr.decision_date,
    }, message="Hiring result fetched")


# ============================================================
# UPDATE HIRING RESULT
# PUT /api/hiring-results/<result_id>/update/
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def hiring_result_update(request, result_id):
    try:
        hr = HiringResult.objects.get(pk=result_id)
    except HiringResult.DoesNotExist:
        return error_response("Hiring result not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "final_score" in data:
        hr.final_score = data["final_score"]
    if "ranking" in data:
        hr.ranking = data["ranking"]

    if "selection_status" in data:
        valid = [c[0] for c in HiringResult.SELECTION_CHOICES]
        if data["selection_status"] not in valid:
            return error_response(f"Invalid selection_status. Allowed: {valid}", status=400)
        hr.selection_status = data["selection_status"]

    if "remarks" in data:
        hr.remarks = data["remarks"]
    if "decision_date" in data:
        hr.decision_date = data["decision_date"]

    hr.save()
    return success_response(
        {"result_id": hr.result_id},
        message="Hiring result updated",
    )


# ============================================================
# DELETE HIRING RESULT
# DELETE /api/hiring-results/<result_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def hiring_result_delete(request, result_id):
    try:
        hr = HiringResult.objects.get(pk=result_id)
    except HiringResult.DoesNotExist:
        return error_response("Hiring result not found", status=404)

    hr.delete()
    return success_response(message="Hiring result deleted")