from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.accounts.models import CandidateProfile
from apps.candidates.models import Resume
from apps.recruitment.models import Job, Application
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# CREATE APPLICATION
# POST /api/applications/create/
# Body: { candidate_id, job_id, resume_id? }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def application_create(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["candidate_id", "job_id"])
    if err:
        return error_response(err, status=400)

    try:
        candidate = CandidateProfile.objects.get(pk=data["candidate_id"])
    except CandidateProfile.DoesNotExist:
        return error_response("Candidate profile not found", status=404)

    try:
        job = Job.objects.get(pk=data["job_id"])
    except Job.DoesNotExist:
        return error_response("Job not found", status=404)

    resume = None
    if data.get("resume_id"):
        try:
            resume = Resume.objects.get(pk=data["resume_id"])
        except Resume.DoesNotExist:
            return error_response("Resume not found", status=404)
        # Resume candidate ka hona chahiye
        if resume.candidate != candidate:
            return error_response("Resume does not belong to this candidate", status=400)

    if Application.objects.filter(candidate=candidate, job=job).exists():
        return error_response("You have already applied for this job", status=409)

    application = Application.objects.create(
        candidate=candidate,
        job=job,
        resume=resume,
    )

    return success_response(
        {
            "application_id": application.application_id,
            "candidate_id": application.candidate.candidate_id,
            "job_id": application.job.job_id,
            "resume_id": application.resume.resume_id if application.resume else None,
            "application_status": application.application_status,
            "applied_at": application.applied_at,
        },
        message="Application submitted",
        status=201,
    )


# ============================================================
# LIST APPLICATIONS
# GET /api/applications/
# ============================================================
@require_http_methods(["GET"])
def application_list(request):
    items = list(
        Application.objects.select_related("candidate", "job", "resume").values(
            "application_id",
            "candidate_id",
            "job_id",
            "resume_id",
            "application_status",
            "applied_at",
        )
    )
    return success_response(items, message="Applications fetched")


# ============================================================
# GET ONE APPLICATION
# GET /api/applications/<application_id>/
# ============================================================
@require_http_methods(["GET"])
def application_detail(request, application_id):
    try:
        app = Application.objects.select_related("candidate__user", "job", "resume").get(pk=application_id)
    except Application.DoesNotExist:
        return error_response("Application not found", status=404)

    return success_response({
        "application_id": app.application_id,
        "candidate_id": app.candidate.candidate_id,
        "candidate_name": app.candidate.user.full_name,
        "candidate_email": app.candidate.user.email,
        "job_id": app.job.job_id,
        "job_title": app.job.job_title,
        "resume_id": app.resume.resume_id if app.resume else None,
        "resume_file": app.resume.file_name if app.resume else None,
        "application_status": app.application_status,
        "applied_at": app.applied_at,
    }, message="Application fetched")


# ============================================================
# UPDATE APPLICATION
# PUT /api/applications/<application_id>/update/
# Body: { application_status?, resume_id? }
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def application_update(request, application_id):
    try:
        app = Application.objects.get(pk=application_id)
    except Application.DoesNotExist:
        return error_response("Application not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "application_status" in data:
        valid = [c[0] for c in Application.STATUS_CHOICES]
        if data["application_status"] not in valid:
            return error_response(f"Invalid status. Allowed: {valid}", status=400)
        app.application_status = data["application_status"]

    if "resume_id" in data:
        if data["resume_id"]:
            try:
                resume = Resume.objects.get(pk=data["resume_id"])
            except Resume.DoesNotExist:
                return error_response("Resume not found", status=404)
            if resume.candidate != app.candidate:
                return error_response("Resume does not belong to this candidate", status=400)
            app.resume = resume
        else:
            app.resume = None

    app.save()
    return success_response(
        {"application_id": app.application_id},
        message="Application updated",
    )


# ============================================================
# DELETE APPLICATION
# DELETE /api/applications/<application_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def application_delete(request, application_id):
    try:
        app = Application.objects.get(pk=application_id)
    except Application.DoesNotExist:
        return error_response("Application not found", status=404)

    app.delete()
    return success_response(message="Application deleted")