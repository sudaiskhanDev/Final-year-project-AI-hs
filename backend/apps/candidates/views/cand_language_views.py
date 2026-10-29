from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.accounts.models import CandidateProfile
from apps.candidates.models import CandLanguage
from apps.masterdata.models import Language
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# CREATE CANDIDATE LANGUAGE
# POST /api/candidate-languages/create/
# Body: { candidate_id, lang_id, proficiency_lvl? }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def cand_language_create(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["candidate_id", "lang_id"])
    if err:
        return error_response(err, status=400)

    try:
        candidate = CandidateProfile.objects.get(pk=data["candidate_id"])
    except CandidateProfile.DoesNotExist:
        return error_response("Candidate profile not found", status=404)

    try:
        language = Language.objects.get(pk=data["lang_id"])
    except Language.DoesNotExist:
        return error_response("Language not found", status=404)

    if CandLanguage.objects.filter(candidate=candidate, language=language).exists():
        return error_response("This candidate already has this language", status=409)

    proficiency = data.get("proficiency_lvl", "intermediate")
    valid = [c[0] for c in CandLanguage.PROFICIENCY_CHOICES]
    if proficiency not in valid:
        return error_response(f"Invalid proficiency. Allowed: {valid}", status=400)

    cl = CandLanguage.objects.create(
        candidate=candidate,
        language=language,
        proficiency_lvl=proficiency,
    )

    return success_response(
        {
            "cand_lang_id": cl.cand_lang_id,
            "candidate_id": cl.candidate.candidate_id,
            "lang_id": cl.language.lang_id,
            "language_name": cl.language.language_name,
            "proficiency_lvl": cl.proficiency_lvl,
        },
        message="Candidate language created",
        status=201,
    )


# ============================================================
# LIST CANDIDATE LANGUAGES
# GET /api/candidate-languages/
# ============================================================
@require_http_methods(["GET"])
def cand_language_list(request):
    items = list(
        CandLanguage.objects.select_related("candidate", "language").values(
            "cand_lang_id",
            "candidate_id",
            "lang_id",
            "language__language_name",
            "proficiency_lvl",
        )
    )
    result = [
        {
            "cand_lang_id": item["cand_lang_id"],
            "candidate_id": item["candidate_id"],
            "lang_id": item["lang_id"],
            "language_name": item["language__language_name"],
            "proficiency_lvl": item["proficiency_lvl"],
        }
        for item in items
    ]
    return success_response(result, message="Candidate languages fetched")


# ============================================================
# GET ONE CANDIDATE LANGUAGE
# GET /api/candidate-languages/<cand_lang_id>/
# ============================================================
@require_http_methods(["GET"])
def cand_language_detail(request, cand_lang_id):
    try:
        cl = CandLanguage.objects.select_related("candidate", "language").get(pk=cand_lang_id)
    except CandLanguage.DoesNotExist:
        return error_response("Candidate language not found", status=404)

    return success_response({
        "cand_lang_id": cl.cand_lang_id,
        "candidate_id": cl.candidate.candidate_id,
        "full_name": cl.candidate.user.full_name,
        "lang_id": cl.language.lang_id,
        "language_name": cl.language.language_name,
        "proficiency_lvl": cl.proficiency_lvl,
    }, message="Candidate language fetched")


# ============================================================
# UPDATE CANDIDATE LANGUAGE
# PUT /api/candidate-languages/<cand_lang_id>/update/
# Body: { lang_id?, proficiency_lvl? }
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def cand_language_update(request, cand_lang_id):
    try:
        cl = CandLanguage.objects.get(pk=cand_lang_id)
    except CandLanguage.DoesNotExist:
        return error_response("Candidate language not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "lang_id" in data:
        try:
            new_lang = Language.objects.get(pk=data["lang_id"])
        except Language.DoesNotExist:
            return error_response("Language not found", status=404)

        if CandLanguage.objects.filter(candidate=cl.candidate, language=new_lang).exclude(pk=cand_lang_id).exists():
            return error_response("This candidate already has this language", status=409)

        cl.language = new_lang

    if "proficiency_lvl" in data:
        valid = [c[0] for c in CandLanguage.PROFICIENCY_CHOICES]
        if data["proficiency_lvl"] not in valid:
            return error_response(f"Invalid proficiency. Allowed: {valid}", status=400)
        cl.proficiency_lvl = data["proficiency_lvl"]

    cl.save()
    return success_response(
        {"cand_lang_id": cl.cand_lang_id},
        message="Candidate language updated",
    )


# ============================================================
# DELETE CANDIDATE LANGUAGE
# DELETE /api/candidate-languages/<cand_lang_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def cand_language_delete(request, cand_lang_id):
    try:
        cl = CandLanguage.objects.get(pk=cand_lang_id)
    except CandLanguage.DoesNotExist:
        return error_response("Candidate language not found", status=404)

    cl.delete()
    return success_response(message="Candidate language deleted")