from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.workflows.utils.apply_job import apply_for_job
from utils.response import success_response, error_response


@csrf_exempt
@require_http_methods(["POST"])
def apply_job_view(request):
    """
    POST /api/workflows/apply-job/
    Form-data:
      - candidate_id (required)
      - job_id (required)
      - file (optional)        -> new CV upload
      - resume_id (optional)   -> existing CV

    At least one of file or resume_id is required.
    """
    candidate_id = request.POST.get("candidate_id")
    job_id = request.POST.get("job_id")
    uploaded_file = request.FILES.get("file")
    resume_id = request.POST.get("resume_id")

    # Validation
    if not candidate_id or not job_id:
        return error_response("candidate_id and job_id are required", status=400)

    if not uploaded_file and not resume_id:
        return error_response("Either 'file' or 'resume_id' is required", status=400)

    try:
        result = apply_for_job(
            candidate_id=int(candidate_id),
            job_id=int(job_id),
            uploaded_file=uploaded_file,
            resume_id=int(resume_id) if resume_id else None,
        )
    except ValueError as e:
        return error_response(str(e), status=400)
    except Exception as e:
        return error_response(f"Server error: {str(e)}", status=500)

    return success_response(result, message="Application submitted", status=201)