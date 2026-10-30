import os
import tempfile

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.ai_services.services.cv_parser import parse_cv
from apps.ai_services.services.question_generator import generate_question
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# GENERATE INTERVIEW QUESTION
# POST /api/ai/generate-question/
# Body: { job_title, job_description, required_experience, skills, question_type? }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def generate_question_view(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["job_title", "job_description", "required_experience", "skills"])
    if err:
        return error_response(err, status=400)

    try:
        question = generate_question(
            job_title=data["job_title"],
            job_description=data["job_description"],
            required_experience=data["required_experience"],
            skills=data["skills"],
            question_type=data.get("question_type", "Scenario"),
        )
    except Exception as e:
        return error_response(f"Model error: {str(e)}", status=500)

    return success_response(
        {"question": question},
        message="Question generated",
    )


# ============================================================
# PARSE CV (upload file)
# POST /api/ai/parse-cv/
# Form-data: file (PDF/DOCX)
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def parse_cv_view(request):
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return error_response("file is required (multipart form-data)", status=400)

    extension = os.path.splitext(uploaded_file.name)[1].lower()
    if extension not in [".pdf", ".docx"]:
        return error_response("Only PDF and DOCX files are allowed", status=400)

    # Temp file banao — parse_cv() path expect karta hai
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        temp_path = temp_file.name

    try:
        result = parse_cv(temp_path)
    except Exception as e:
        return error_response(f"Parsing error: {str(e)}", status=500)
    finally:
        try:
            os.unlink(temp_path)
        except Exception:
            pass

    return success_response(result, message="CV parsed successfully")


# ============================================================
# PARSE CV (existing resume by ID)
# POST /api/ai/parse-cv/<resume_id>/
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def parse_cv_by_resume_id_view(request, resume_id):
    # Lazy import — circular dependency avoid karne ke liye
    from apps.candidates.models import Resume

    try:
        resume = Resume.objects.select_related("candidate__user").get(pk=resume_id)
    except Resume.DoesNotExist:
        return error_response("Resume not found", status=404)

    # Auth check — resume kis candidate ka hai
    if not request.user.is_authenticated:
        return error_response("Authentication required", status=401)

    if resume.candidate.user != request.user:
        return error_response("This resume does not belong to you", status=403)

    if not resume.file_path:
        return error_response("Resume file path is missing", status=404)

    # DB mein file_path "/media/resumes/xyz.pdf" hai → absolute path banao
    relative = resume.file_path.replace(settings.MEDIA_URL, "", 1)
    absolute_path = os.path.join(settings.MEDIA_ROOT, relative)

    if not os.path.exists(absolute_path):
        return error_response(f"Resume file not found on disk: {absolute_path}", status=404)

    try:
        result = parse_cv(absolute_path)
    except Exception as e:
        return error_response(f"Parsing error: {str(e)}", status=500)

    return success_response(result, message="CV parsed successfully")