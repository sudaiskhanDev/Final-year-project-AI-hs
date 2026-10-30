from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.masterdata.models import Qualification
from apps.recruitment.models import Job, JobQualification
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# CREATE JOB QUALIFICATION
# POST /api/job-qualifications/create/
# Body: { job_id, qualification_id }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def job_qualification_create(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["job_id", "qualification_id"])
    if err:
        return error_response(err, status=400)

    try:
        job = Job.objects.get(pk=data["job_id"])
    except Job.DoesNotExist:
        return error_response("Job not found", status=404)

    try:
        qualification = Qualification.objects.get(pk=data["qualification_id"])
    except Qualification.DoesNotExist:
        return error_response("Qualification not found", status=404)

    if JobQualification.objects.filter(job=job, qualification=qualification).exists():
        return error_response("This job already has this qualification", status=409)

    jq = JobQualification.objects.create(job=job, qualification=qualification)

    return success_response(
        {
            "job_qualification_id": jq.job_qualification_id,
            "job_id": jq.job.job_id,
            "qualification_id": jq.qualification.qualification_id,
            "qualification_name": jq.qualification.qualification_name,
        },
        message="Job qualification created",
        status=201,
    )


# ============================================================
# LIST JOB QUALIFICATIONS
# GET /api/job-qualifications/
# ============================================================
@require_http_methods(["GET"])
def job_qualification_list(request):
    items = list(
        JobQualification.objects.select_related("job", "qualification").values(
            "job_qualification_id",
            "job_id",
            "qualification_id",
            "qualification__qualification_name",
        )
    )
    result = [
        {
            "job_qualification_id": item["job_qualification_id"],
            "job_id": item["job_id"],
            "qualification_id": item["qualification_id"],
            "qualification_name": item["qualification__qualification_name"],
        }
        for item in items
    ]
    return success_response(result, message="Job qualifications fetched")


# ============================================================
# GET ONE JOB QUALIFICATION
# GET /api/job-qualifications/<job_qualification_id>/
# ============================================================
@require_http_methods(["GET"])
def job_qualification_detail(request, job_qualification_id):
    try:
        jq = JobQualification.objects.select_related("job", "qualification").get(pk=job_qualification_id)
    except JobQualification.DoesNotExist:
        return error_response("Job qualification not found", status=404)

    return success_response({
        "job_qualification_id": jq.job_qualification_id,
        "job_id": jq.job.job_id,
        "job_title": jq.job.job_title,
        "qualification_id": jq.qualification.qualification_id,
        "qualification_name": jq.qualification.qualification_name,
    }, message="Job qualification fetched")


# ============================================================
# UPDATE JOB QUALIFICATION — change qualification
# PUT /api/job-qualifications/<job_qualification_id>/update/
# Body: { qualification_id }
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def job_qualification_update(request, job_qualification_id):
    try:
        jq = JobQualification.objects.get(pk=job_qualification_id)
    except JobQualification.DoesNotExist:
        return error_response("Job qualification not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "qualification_id" in data:
        try:
            new_qual = Qualification.objects.get(pk=data["qualification_id"])
        except Qualification.DoesNotExist:
            return error_response("Qualification not found", status=404)

        if JobQualification.objects.filter(job=jq.job, qualification=new_qual).exclude(pk=job_qualification_id).exists():
            return error_response("This job already has this qualification", status=409)

        jq.qualification = new_qual
        jq.save()

    return success_response(
        {"job_qualification_id": jq.job_qualification_id},
        message="Job qualification updated",
    )


# ============================================================
# DELETE JOB QUALIFICATION
# DELETE /api/job-qualifications/<job_qualification_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def job_qualification_delete(request, job_qualification_id):
    try:
        jq = JobQualification.objects.get(pk=job_qualification_id)
    except JobQualification.DoesNotExist:
        return error_response("Job qualification not found", status=404)

    jq.delete()
    return success_response(message="Job qualification deleted")