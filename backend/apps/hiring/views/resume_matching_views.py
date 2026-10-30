from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.recruitment.models import Application
from apps.hiring.models import ResumeMatching
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# CREATE RESUME MATCHING
# POST /api/resume-matchings/create/
# Body: { application_id, skills_score?, experience_score?, qualification_score?, total_score?, status? }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def resume_matching_create(request):
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

    if ResumeMatching.objects.filter(application=application).exists():
        return error_response("Resume matching already exists for this application", status=409)

    status_val = data.get("status", "pending")
    valid = [c[0] for c in ResumeMatching.STATUS_CHOICES]
    if status_val not in valid:
        return error_response(f"Invalid status. Allowed: {valid}", status=400)

    evaluated_at = None
    if status_val == "completed":
        evaluated_at = timezone.now()

    rm = ResumeMatching.objects.create(
        application=application,
        skills_score=data.get("skills_score", 0),
        experience_score=data.get("experience_score", 0),
        qualification_score=data.get("qualification_score", 0),
        total_score=data.get("total_score", 0),
        status=status_val,
        evaluated_at=evaluated_at,
    )

    return success_response(
        {
            "matching_id": rm.matching_id,
            "application_id": rm.application.application_id,
            "skills_score": str(rm.skills_score),
            "experience_score": str(rm.experience_score),
            "qualification_score": str(rm.qualification_score),
            "total_score": str(rm.total_score),
            "status": rm.status,
            "evaluated_at": rm.evaluated_at,
        },
        message="Resume matching created",
        status=201,
    )


# ============================================================
# LIST RESUME MATCHINGS
# GET /api/resume-matchings/
# ============================================================
@require_http_methods(["GET"])
def resume_matching_list(request):
    items = list(
        ResumeMatching.objects.select_related("application").values(
            "matching_id",
            "application_id",
            "skills_score",
            "experience_score",
            "qualification_score",
            "total_score",
            "status",
            "evaluated_at",
        )
    )
    for item in items:
        item["skills_score"] = str(item["skills_score"])
        item["experience_score"] = str(item["experience_score"])
        item["qualification_score"] = str(item["qualification_score"])
        item["total_score"] = str(item["total_score"])
    return success_response(items, message="Resume matchings fetched")


# ============================================================
# GET ONE RESUME MATCHING
# GET /api/resume-matchings/<matching_id>/
# ============================================================
@require_http_methods(["GET"])
def resume_matching_detail(request, matching_id):
    try:
        rm = ResumeMatching.objects.select_related(
            "application__candidate__user",
            "application__job",
        ).get(pk=matching_id)
    except ResumeMatching.DoesNotExist:
        return error_response("Resume matching not found", status=404)

    return success_response({
        "matching_id": rm.matching_id,
        "application_id": rm.application.application_id,
        "candidate_name": rm.application.candidate.user.full_name,
        "job_title": rm.application.job.job_title,
        "skills_score": str(rm.skills_score),
        "experience_score": str(rm.experience_score),
        "qualification_score": str(rm.qualification_score),
        "total_score": str(rm.total_score),
        "status": rm.status,
        "evaluated_at": rm.evaluated_at,
    }, message="Resume matching fetched")


# ============================================================
# UPDATE RESUME MATCHING
# PUT /api/resume-matchings/<matching_id>/update/
# Body: { skills_score?, experience_score?, qualification_score?, total_score?, status? }
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def resume_matching_update(request, matching_id):
    try:
        rm = ResumeMatching.objects.get(pk=matching_id)
    except ResumeMatching.DoesNotExist:
        return error_response("Resume matching not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "skills_score" in data:
        rm.skills_score = data["skills_score"]
    if "experience_score" in data:
        rm.experience_score = data["experience_score"]
    if "qualification_score" in data:
        rm.qualification_score = data["qualification_score"]
    if "total_score" in data:
        rm.total_score = data["total_score"]

    if "status" in data:
        valid = [c[0] for c in ResumeMatching.STATUS_CHOICES]
        if data["status"] not in valid:
            return error_response(f"Invalid status. Allowed: {valid}", status=400)
        rm.status = data["status"]
        # Auto-set evaluated_at when completed
        if data["status"] == "completed" and not rm.evaluated_at:
            rm.evaluated_at = timezone.now()

    rm.save()
    return success_response(
        {"matching_id": rm.matching_id},
        message="Resume matching updated",
    )


# ============================================================
# DELETE RESUME MATCHING
# DELETE /api/resume-matchings/<matching_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def resume_matching_delete(request, matching_id):
    try:
        rm = ResumeMatching.objects.get(pk=matching_id)
    except ResumeMatching.DoesNotExist:
        return error_response("Resume matching not found", status=404)

    rm.delete()
    return success_response(message="Resume matching deleted")