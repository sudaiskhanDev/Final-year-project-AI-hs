from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.accounts.models import HRProfile
from apps.recruitment.models import Job
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# CREATE JOB
# POST /api/jobs/create/
# Body: { hr_id, job_title, job_description, required_exp, minimum_score, due_date }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def job_create(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["hr_id", "job_title", "job_description", "due_date"])
    if err:
        return error_response(err, status=400)

    try:
        hr = HRProfile.objects.get(pk=data["hr_id"])
    except HRProfile.DoesNotExist:
        return error_response("HR profile not found", status=404)

    job = Job.objects.create(
        hr=hr,
        job_title=data["job_title"],
        job_description=data["job_description"],
        required_exp=data.get("required_exp", 0),
        minimum_score=data.get("minimum_score", 0),
        due_date=data["due_date"],
    )

    return success_response(
        {
            "job_id": job.job_id,
            "hr_id": job.hr.hr_id,
            "job_title": job.job_title,
            "job_description": job.job_description,
            "required_exp": str(job.required_exp),
            "minimum_score": str(job.minimum_score),
            "due_date": job.due_date,
            "created_at": job.created_at,
        },
        message="Job created",
        status=201,
    )


# ============================================================
# LIST JOBS
# GET /api/jobs/
# ============================================================
@require_http_methods(["GET"])
def job_list(request):
    jobs = list(
        Job.objects.select_related("hr").values(
            "job_id",
            "hr_id",
            "job_title",
            "job_description",
            "required_exp",
            "minimum_score",
            "due_date",
            "created_at",
        )
    )
    # Decimal ko string mein convert (JSON serialization ke liye)
    for j in jobs:
        j["required_exp"] = str(j["required_exp"])
        j["minimum_score"] = str(j["minimum_score"])
    return success_response(jobs, message="Jobs fetched")


# ============================================================
# GET ONE JOB
# GET /api/jobs/<job_id>/
# ============================================================
@require_http_methods(["GET"])
def job_detail(request, job_id):
    try:
        job = Job.objects.select_related("hr").get(pk=job_id)
    except Job.DoesNotExist:
        return error_response("Job not found", status=404)

    return success_response({
        "job_id": job.job_id,
        "hr_id": job.hr.hr_id,
        "hr_name": job.hr.user.full_name,
        "hr_email": job.hr.user.email,
        "department": job.hr.department,
        "job_title": job.job_title,
        "job_description": job.job_description,
        "required_exp": str(job.required_exp),
        "minimum_score": str(job.minimum_score),
        "due_date": job.due_date,
        "created_at": job.created_at,
    }, message="Job fetched")


# ============================================================
# UPDATE JOB
# PUT /api/jobs/<job_id>/update/
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def job_update(request, job_id):
    try:
        job = Job.objects.get(pk=job_id)
    except Job.DoesNotExist:
        return error_response("Job not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "job_title" in data:
        job.job_title = data["job_title"]
    if "job_description" in data:
        job.job_description = data["job_description"]
    if "required_exp" in data:
        job.required_exp = data["required_exp"]
    if "minimum_score" in data:
        job.minimum_score = data["minimum_score"]
    if "due_date" in data:
        job.due_date = data["due_date"]

    job.save()
    return success_response(
        {"job_id": job.job_id},
        message="Job updated",
    )


# ============================================================
# DELETE JOB
# DELETE /api/jobs/<job_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def job_delete(request, job_id):
    try:
        job = Job.objects.get(pk=job_id)
    except Job.DoesNotExist:
        return error_response("Job not found", status=404)

    job.delete()
    return success_response(message="Job deleted")