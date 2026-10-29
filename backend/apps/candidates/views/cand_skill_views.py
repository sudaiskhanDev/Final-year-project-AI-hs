from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.accounts.models import CandidateProfile
from apps.candidates.models import CandidateSkill
from apps.masterdata.models import Skill
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# CREATE CANDIDATE SKILL
# POST /api/candidate-skills/create/
# Body: { candidate_id, skill_id }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def cand_skill_create(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["candidate_id", "skill_id"])
    if err:
        return error_response(err, status=400)

    try:
        candidate = CandidateProfile.objects.get(pk=data["candidate_id"])
    except CandidateProfile.DoesNotExist:
        return error_response("Candidate profile not found", status=404)

    try:
        skill = Skill.objects.get(pk=data["skill_id"])
    except Skill.DoesNotExist:
        return error_response("Skill not found", status=404)

    # Duplicate check (unique_together)
    if CandidateSkill.objects.filter(candidate=candidate, skill=skill).exists():
        return error_response("This candidate already has this skill", status=409)

    cs = CandidateSkill.objects.create(candidate=candidate, skill=skill)

    return success_response(
        {
            "candidate_skill_id": cs.candidate_skill_id,
            "candidate_id": cs.candidate.candidate_id,
            "skill_id": cs.skill.skill_id,
            "skill_name": cs.skill.skill_name,
        },
        message="Candidate skill created",
        status=201,
    )


# ============================================================
# LIST CANDIDATE SKILLS
# GET /api/candidate-skills/
# ============================================================
@require_http_methods(["GET"])
def cand_skill_list(request):
    items = list(
        CandidateSkill.objects.select_related("candidate", "skill").values(
            "candidate_skill_id",
            "candidate_id",
            "skill_id",
            "skill__skill_name",
        )
    )
    # Format output (skill__skill_name → skill_name)
    result = [
        {
            "candidate_skill_id": item["candidate_skill_id"],
            "candidate_id": item["candidate_id"],
            "skill_id": item["skill_id"],
            "skill_name": item["skill__skill_name"],
        }
        for item in items
    ]
    return success_response(result, message="Candidate skills fetched")


# ============================================================
# GET ONE CANDIDATE SKILL
# GET /api/candidate-skills/<candidate_skill_id>/
# ============================================================
@require_http_methods(["GET"])
def cand_skill_detail(request, candidate_skill_id):
    try:
        cs = CandidateSkill.objects.select_related("candidate", "skill").get(pk=candidate_skill_id)
    except CandidateSkill.DoesNotExist:
        return error_response("Candidate skill not found", status=404)

    return success_response({
        "candidate_skill_id": cs.candidate_skill_id,
        "candidate_id": cs.candidate.candidate_id,
        "full_name": cs.candidate.user.full_name,
        "skill_id": cs.skill.skill_id,
        "skill_name": cs.skill.skill_name,
    }, message="Candidate skill fetched")


# ============================================================
# UPDATE CANDIDATE SKILL — change skill
# PUT /api/candidate-skills/<candidate_skill_id>/update/
# Body: { skill_id }
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def cand_skill_update(request, candidate_skill_id):
    try:
        cs = CandidateSkill.objects.get(pk=candidate_skill_id)
    except CandidateSkill.DoesNotExist:
        return error_response("Candidate skill not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "skill_id" in data:
        try:
            new_skill = Skill.objects.get(pk=data["skill_id"])
        except Skill.DoesNotExist:
            return error_response("Skill not found", status=404)

        if CandidateSkill.objects.filter(candidate=cs.candidate, skill=new_skill).exclude(pk=candidate_skill_id).exists():
            return error_response("This candidate already has this skill", status=409)

        cs.skill = new_skill
        cs.save()

    return success_response(
        {"candidate_skill_id": cs.candidate_skill_id},
        message="Candidate skill updated",
    )


# ============================================================
# DELETE CANDIDATE SKILL
# DELETE /api/candidate-skills/<candidate_skill_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def cand_skill_delete(request, candidate_skill_id):
    try:
        cs = CandidateSkill.objects.get(pk=candidate_skill_id)
    except CandidateSkill.DoesNotExist:
        return error_response("Candidate skill not found", status=404)

    cs.delete()
    return success_response(message="Candidate skill deleted")