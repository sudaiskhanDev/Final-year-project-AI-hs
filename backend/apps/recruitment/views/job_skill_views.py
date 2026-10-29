from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.masterdata.models import Skill
from apps.recruitment.models import Job, JobSkill
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# CREATE JOB SKILL
# POST /api/job-skills/create/
# Body: { job_id, skill_id }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def job_skill_create(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["job_id", "skill_id"])
    if err:
        return error_response(err, status=400)

    try:
        job = Job.objects.get(pk=data["job_id"])
    except Job.DoesNotExist:
        return error_response("Job not found", status=404)

    try:
        skill = Skill.objects.get(pk=data["skill_id"])
    except Skill.DoesNotExist:
        return error_response("Skill not found", status=404)

    if JobSkill.objects.filter(job=job, skill=skill).exists():
        return error_response("This job already has this skill", status=409)

    js = JobSkill.objects.create(job=job, skill=skill)

    return success_response(
        {
            "job_skill_id": js.job_skill_id,
            "job_id": js.job.job_id,
            "skill_id": js.skill.skill_id,
            "skill_name": js.skill.skill_name,
        },
        message="Job skill created",
        status=201,
    )


# ============================================================
# LIST JOB SKILLS
# GET /api/job-skills/
# ============================================================
@require_http_methods(["GET"])
def job_skill_list(request):
    items = list(
        JobSkill.objects.select_related("job", "skill").values(
            "job_skill_id",
            "job_id",
            "skill_id",
            "skill__skill_name",
        )
    )
    result = [
        {
            "job_skill_id": item["job_skill_id"],
            "job_id": item["job_id"],
            "skill_id": item["skill_id"],
            "skill_name": item["skill__skill_name"],
        }
        for item in items
    ]
    return success_response(result, message="Job skills fetched")


# ============================================================
# GET ONE JOB SKILL
# GET /api/job-skills/<job_skill_id>/
# ============================================================
@require_http_methods(["GET"])
def job_skill_detail(request, job_skill_id):
    try:
        js = JobSkill.objects.select_related("job", "skill").get(pk=job_skill_id)
    except JobSkill.DoesNotExist:
        return error_response("Job skill not found", status=404)

    return success_response({
        "job_skill_id": js.job_skill_id,
        "job_id": js.job.job_id,
        "job_title": js.job.job_title,
        "skill_id": js.skill.skill_id,
        "skill_name": js.skill.skill_name,
    }, message="Job skill fetched")


# ============================================================
# UPDATE JOB SKILL — change skill
# PUT /api/job-skills/<job_skill_id>/update/
# Body: { skill_id }
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def job_skill_update(request, job_skill_id):
    try:
        js = JobSkill.objects.get(pk=job_skill_id)
    except JobSkill.DoesNotExist:
        return error_response("Job skill not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "skill_id" in data:
        try:
            new_skill = Skill.objects.get(pk=data["skill_id"])
        except Skill.DoesNotExist:
            return error_response("Skill not found", status=404)

        if JobSkill.objects.filter(job=js.job, skill=new_skill).exclude(pk=job_skill_id).exists():
            return error_response("This job already has this skill", status=409)

        js.skill = new_skill
        js.save()

    return success_response(
        {"job_skill_id": js.job_skill_id},
        message="Job skill updated",
    )


# ============================================================
# DELETE JOB SKILL
# DELETE /api/job-skills/<job_skill_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def job_skill_delete(request, job_skill_id):
    try:
        js = JobSkill.objects.get(pk=job_skill_id)
    except JobSkill.DoesNotExist:
        return error_response("Job skill not found", status=404)

    js.delete()
    return success_response(message="Job skill deleted")