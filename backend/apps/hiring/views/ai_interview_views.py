from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.recruitment.models import Application
from apps.hiring.models import AIInterview
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# CREATE AI INTERVIEW
# POST /api/ai-interviews/create/
# Body: { application_id, interview_mode?, interview_round?, video_path?, overall_score?, interview_status?, started_at?, completed_at? }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def ai_interview_create(request):
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

    mode = data.get("interview_mode", "ai")
    valid_modes = [c[0] for c in AIInterview.MODE_CHOICES]
    if mode not in valid_modes:
        return error_response(f"Invalid mode. Allowed: {valid_modes}", status=400)

    status_val = data.get("interview_status", "pending")
    valid_statuses = [c[0] for c in AIInterview.STATUS_CHOICES]
    if status_val not in valid_statuses:
        return error_response(f"Invalid status. Allowed: {valid_statuses}", status=400)

    started_at = None
    completed_at = None
    if status_val == "in_progress" and not data.get("started_at"):
        started_at = timezone.now()
    elif data.get("started_at"):
        started_at = data["started_at"]

    if status_val == "completed" and not data.get("completed_at"):
        completed_at = timezone.now()
    elif data.get("completed_at"):
        completed_at = data["completed_at"]

    interview = AIInterview.objects.create(
        application=application,
        interview_mode=mode,
        interview_round=data.get("interview_round", "1st Round"),
        video_path=data.get("video_path"),
        overall_score=data.get("overall_score", 0),
        interview_status=status_val,
        started_at=started_at,
        completed_at=completed_at,
    )

    return success_response(
        {
            "interview_id": interview.interview_id,
            "application_id": interview.application.application_id,
            "interview_mode": interview.interview_mode,
            "interview_round": interview.interview_round,
            "video_path": interview.video_path,
            "overall_score": str(interview.overall_score),
            "interview_status": interview.interview_status,
            "started_at": interview.started_at,
            "completed_at": interview.completed_at,
        },
        message="Interview created",
        status=201,
    )


# ============================================================
# LIST AI INTERVIEWS
# GET /api/ai-interviews/
# ============================================================
@require_http_methods(["GET"])
def ai_interview_list(request):
    items = list(
        AIInterview.objects.select_related("application").values(
            "interview_id",
            "application_id",
            "interview_mode",
            "interview_round",
            "video_path",
            "overall_score",
            "interview_status",
            "started_at",
            "completed_at",
        )
    )
    for item in items:
        item["overall_score"] = str(item["overall_score"])
    return success_response(items, message="Interviews fetched")


# ============================================================
# GET ONE AI INTERVIEW
# GET /api/ai-interviews/<interview_id>/
# ============================================================
@require_http_methods(["GET"])
def ai_interview_detail(request, interview_id):
    try:
        interview = AIInterview.objects.select_related(
            "application__candidate__user",
            "application__job",
        ).get(pk=interview_id)
    except AIInterview.DoesNotExist:
        return error_response("Interview not found", status=404)

    return success_response({
        "interview_id": interview.interview_id,
        "application_id": interview.application.application_id,
        "candidate_name": interview.application.candidate.user.full_name,
        "job_title": interview.application.job.job_title,
        "interview_mode": interview.interview_mode,
        "interview_round": interview.interview_round,
        "video_path": interview.video_path,
        "overall_score": str(interview.overall_score),
        "interview_status": interview.interview_status,
        "started_at": interview.started_at,
        "completed_at": interview.completed_at,
    }, message="Interview fetched")


# ============================================================
# UPDATE AI INTERVIEW
# PUT /api/ai-interviews/<interview_id>/update/
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def ai_interview_update(request, interview_id):
    try:
        interview = AIInterview.objects.get(pk=interview_id)
    except AIInterview.DoesNotExist:
        return error_response("Interview not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "interview_mode" in data:
        valid = [c[0] for c in AIInterview.MODE_CHOICES]
        if data["interview_mode"] not in valid:
            return error_response(f"Invalid mode. Allowed: {valid}", status=400)
        interview.interview_mode = data["interview_mode"]

    if "interview_round" in data:
        interview.interview_round = data["interview_round"]
    if "video_path" in data:
        interview.video_path = data["video_path"]
    if "overall_score" in data:
        interview.overall_score = data["overall_score"]

    if "interview_status" in data:
        valid = [c[0] for c in AIInterview.STATUS_CHOICES]
        if data["interview_status"] not in valid:
            return error_response(f"Invalid status. Allowed: {valid}", status=400)
        interview.interview_status = data["interview_status"]
        # Auto-set timestamps
        if data["interview_status"] == "in_progress" and not interview.started_at:
            interview.started_at = timezone.now()
        if data["interview_status"] == "completed" and not interview.completed_at:
            interview.completed_at = timezone.now()

    if "started_at" in data:
        interview.started_at = data["started_at"]
    if "completed_at" in data:
        interview.completed_at = data["completed_at"]

    interview.save()
    return success_response(
        {"interview_id": interview.interview_id},
        message="Interview updated",
    )


# ============================================================
# DELETE AI INTERVIEW
# DELETE /api/ai-interviews/<interview_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def ai_interview_delete(request, interview_id):
    try:
        interview = AIInterview.objects.get(pk=interview_id)
    except AIInterview.DoesNotExist:
        return error_response("Interview not found", status=404)

    interview.delete()
    return success_response(message="Interview deleted")