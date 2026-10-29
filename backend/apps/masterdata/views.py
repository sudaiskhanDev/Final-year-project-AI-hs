from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.masterdata.models import Skill, Qualification, Language
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# SKILLS — CRUD
# ============================================================

@csrf_exempt
@require_http_methods(["GET", "POST"])
def skill_list_create(request):
    if request.method == "GET":
        skills = list(Skill.objects.values("skill_id", "skill_name", "created_at"))
        return success_response(skills, message="Skills fetched")

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["skill_name"])
    if err:
        return error_response(err, status=400)

    name = data["skill_name"].strip()
    if Skill.objects.filter(skill_name__iexact=name).exists():
        return error_response("Skill already exists", status=409)

    skill = Skill.objects.create(skill_name=name)
    return success_response(
        {"skill_id": skill.skill_id, "skill_name": skill.skill_name},
        message="Skill created",
        status=201,
    )


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def skill_detail(request, skill_id):
    try:
        skill = Skill.objects.get(pk=skill_id)
    except Skill.DoesNotExist:
        return error_response("Skill not found", status=404)

    if request.method == "GET":
        return success_response({
            "skill_id": skill.skill_id,
            "skill_name": skill.skill_name,
            "created_at": skill.created_at,
        }, message="Skill fetched")

    if request.method in ("PUT", "PATCH"):
        data, err = parse_json(request)
        if err:
            return error_response(err, status=400)

        if "skill_name" in data:
            name = data["skill_name"].strip()
            if Skill.objects.filter(skill_name__iexact=name).exclude(pk=skill_id).exists():
                return error_response("Skill name already in use", status=409)
            skill.skill_name = name
        skill.save()
        return success_response({"skill_id": skill.skill_id}, message="Skill updated")

    skill.delete()
    return success_response(message="Skill deleted")


# ============================================================
# QUALIFICATIONS — CRUD
# ============================================================

@csrf_exempt
@require_http_methods(["GET", "POST"])
def qualification_list_create(request):
    if request.method == "GET":
        items = list(Qualification.objects.values("qualification_id", "qualification_name", "created_at"))
        return success_response(items, message="Qualifications fetched")

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["qualification_name"])
    if err:
        return error_response(err, status=400)

    name = data["qualification_name"].strip()
    if Qualification.objects.filter(qualification_name__iexact=name).exists():
        return error_response("Qualification already exists", status=409)

    q = Qualification.objects.create(qualification_name=name)
    return success_response(
        {"qualification_id": q.qualification_id, "qualification_name": q.qualification_name},
        message="Qualification created",
        status=201,
    )


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def qualification_detail(request, qualification_id):
    try:
        q = Qualification.objects.get(pk=qualification_id)
    except Qualification.DoesNotExist:
        return error_response("Qualification not found", status=404)

    if request.method == "GET":
        return success_response({
            "qualification_id": q.qualification_id,
            "qualification_name": q.qualification_name,
            "created_at": q.created_at,
        }, message="Qualification fetched")

    if request.method in ("PUT", "PATCH"):
        data, err = parse_json(request)
        if err:
            return error_response(err, status=400)

        if "qualification_name" in data:
            name = data["qualification_name"].strip()
            if Qualification.objects.filter(qualification_name__iexact=name).exclude(pk=qualification_id).exists():
                return error_response("Qualification name already in use", status=409)
            q.qualification_name = name
        q.save()
        return success_response({"qualification_id": q.qualification_id}, message="Qualification updated")

    q.delete()
    return success_response(message="Qualification deleted")


# ============================================================
# LANGUAGES — CRUD
# ============================================================

@csrf_exempt
@require_http_methods(["GET", "POST"])
def language_list_create(request):
    if request.method == "GET":
        items = list(Language.objects.values("lang_id", "language_name", "created_at"))
        return success_response(items, message="Languages fetched")

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["language_name"])
    if err:
        return error_response(err, status=400)

    name = data["language_name"].strip()
    if Language.objects.filter(language_name__iexact=name).exists():
        return error_response("Language already exists", status=409)

    lang = Language.objects.create(language_name=name)
    return success_response(
        {"lang_id": lang.lang_id, "language_name": lang.language_name},
        message="Language created",
        status=201,
    )


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def language_detail(request, lang_id):
    try:
        lang = Language.objects.get(pk=lang_id)
    except Language.DoesNotExist:
        return error_response("Language not found", status=404)

    if request.method == "GET":
        return success_response({
            "lang_id": lang.lang_id,
            "language_name": lang.language_name,
            "created_at": lang.created_at,
        }, message="Language fetched")

    if request.method in ("PUT", "PATCH"):
        data, err = parse_json(request)
        if err:
            return error_response(err, status=400)

        if "language_name" in data:
            name = data["language_name"].strip()
            if Language.objects.filter(language_name__iexact=name).exclude(pk=lang_id).exists():
                return error_response("Language name already in use", status=409)
            lang.language_name = name
        lang.save()
        return success_response({"lang_id": lang.lang_id}, message="Language updated")

    lang.delete()
    return success_response(message="Language deleted")