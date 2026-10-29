import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.accounts.models import CandidateProfile
from apps.candidates.models import Resume
from utils.response import success_response, error_response
# ============================================================
# CREATE RESUME
# POST /api/resumes/create/
# Body: { candidate_id, file_name, file_path }
# ============================================================

# ============================================================
# CREATE RESUME — with file upload (multipart/form-data)
# POST /api/resumes/create/
# Form fields: candidate_id, file (file input)
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def resume_create(request):
    candidate_id = request.POST.get("candidate_id")
    uploaded_file = request.FILES.get("file")

    if not candidate_id:
        return error_response("candidate_id is required", status=400)

    if not uploaded_file:
        return error_response("file is required", status=400)

    try:
        candidate = CandidateProfile.objects.get(pk=candidate_id)
    except CandidateProfile.DoesNotExist:
        return error_response("Candidate profile not found", status=404)

    # File ko media/resumes/ mein save karo
    save_path = os.path.join("resumes", uploaded_file.name)
    saved_path = default_storage.save(save_path, ContentFile(uploaded_file.read()))

    # Public URL
    file_url = settings.MEDIA_URL + saved_path

    resume = Resume.objects.create(
        candidate=candidate,
        file_name=uploaded_file.name,
        file_path=file_url,
    )

    return success_response(
        {
            "resume_id": resume.resume_id,
            "candidate_id": resume.candidate.candidate_id,
            "file_name": resume.file_name,
            "file_path": resume.file_path,
            "uploaded_at": resume.uploaded_at,
        },
        message="Resume uploaded",
        status=201,
    )


# ============================================================
# LIST RESUMES
# GET /api/resumes/
# ============================================================
@require_http_methods(["GET"])
def resume_list(request):
    resumes = list(
        Resume.objects.values(
            "resume_id", "candidate_id", "file_name", "file_path", "uploaded_at",
        )
    )
    return success_response(resumes, message="Resumes fetched")


# ============================================================
# GET ONE RESUME
# GET /api/resumes/<resume_id>/
# ============================================================
@require_http_methods(["GET"])
def resume_detail(request, resume_id):
    try:
        resume = Resume.objects.select_related("candidate").get(pk=resume_id)
    except Resume.DoesNotExist:
        return error_response("Resume not found", status=404)

    return success_response({
        "resume_id": resume.resume_id,
        "candidate_id": resume.candidate.candidate_id,
        "full_name": resume.candidate.user.full_name,
        "email": resume.candidate.user.email,
        "file_name": resume.file_name,
        "file_path": resume.file_path,
        "uploaded_at": resume.uploaded_at,
    }, message="Resume fetched")


# ============================================================
# UPDATE RESUME
# PUT /api/resumes/<resume_id>/update/
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def resume_update(request, resume_id):
    try:
        resume = Resume.objects.get(pk=resume_id)
    except Resume.DoesNotExist:
        return error_response("Resume not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "file_name" in data:
        resume.file_name = data["file_name"]
    if "file_path" in data:
        resume.file_path = data["file_path"]

    resume.save()
    return success_response(
        {"resume_id": resume.resume_id},
        message="Resume updated",
    )


# ============================================================
# DELETE RESUME
# DELETE /api/resumes/<resume_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def resume_delete(request, resume_id):
    try:
        resume = Resume.objects.get(pk=resume_id)
    except Resume.DoesNotExist:
        return error_response("Resume not found", status=404)

    resume.delete()
    return success_response(message="Resume deleted")