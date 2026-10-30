from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.hiring.models import AIInterview, VideoAnalysis
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# CREATE VIDEO ANALYSIS
# POST /api/video-analyses/create/
# Body: { interview_id, eye_contact_score?, dress_code?, dress_score?, confidence_score?, overall_video_score? }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def video_analysis_create(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["interview_id"])
    if err:
        return error_response(err, status=400)

    try:
        interview = AIInterview.objects.get(pk=data["interview_id"])
    except AIInterview.DoesNotExist:
        return error_response("Interview not found", status=404)

    if VideoAnalysis.objects.filter(interview=interview).exists():
        return error_response("Video analysis already exists for this interview", status=409)

    va = VideoAnalysis.objects.create(
        interview=interview,
        eye_contact_score=data.get("eye_contact_score", 0),
        dress_code=data.get("dress_code"),
        dress_score=data.get("dress_score", 0),
        confidence_score=data.get("confidence_score", 0),
        overall_video_score=data.get("overall_video_score", 0),
        analyzed_at=timezone.now(),
    )

    return success_response(
        {
            "analysis_id": va.analysis_id,
            "interview_id": va.interview.interview_id,
            "eye_contact_score": str(va.eye_contact_score),
            "dress_code": va.dress_code,
            "dress_score": str(va.dress_score),
            "confidence_score": str(va.confidence_score),
            "overall_video_score": str(va.overall_video_score),
            "analyzed_at": va.analyzed_at,
        },
        message="Video analysis created",
        status=201,
    )


# ============================================================
# LIST VIDEO ANALYSES
# GET /api/video-analyses/
# ============================================================
@require_http_methods(["GET"])
def video_analysis_list(request):
    items = list(
        VideoAnalysis.objects.select_related("interview").values(
            "analysis_id",
            "interview_id",
            "eye_contact_score",
            "dress_code",
            "dress_score",
            "confidence_score",
            "overall_video_score",
            "analyzed_at",
        )
    )
    for item in items:
        item["eye_contact_score"] = str(item["eye_contact_score"])
        item["dress_score"] = str(item["dress_score"])
        item["confidence_score"] = str(item["confidence_score"])
        item["overall_video_score"] = str(item["overall_video_score"])
    return success_response(items, message="Video analyses fetched")


# ============================================================
# GET ONE VIDEO ANALYSIS
# GET /api/video-analyses/<analysis_id>/
# ============================================================
@require_http_methods(["GET"])
def video_analysis_detail(request, analysis_id):
    try:
        va = VideoAnalysis.objects.select_related(
            "interview__application__candidate__user",
            "interview__application__job",
        ).get(pk=analysis_id)
    except VideoAnalysis.DoesNotExist:
        return error_response("Video analysis not found", status=404)

    return success_response({
        "analysis_id": va.analysis_id,
        "interview_id": va.interview.interview_id,
        "candidate_name": va.interview.application.candidate.user.full_name,
        "job_title": va.interview.application.job.job_title,
        "eye_contact_score": str(va.eye_contact_score),
        "dress_code": va.dress_code,
        "dress_score": str(va.dress_score),
        "confidence_score": str(va.confidence_score),
        "overall_video_score": str(va.overall_video_score),
        "analyzed_at": va.analyzed_at,
    }, message="Video analysis fetched")


# ============================================================
# UPDATE VIDEO ANALYSIS
# PUT /api/video-analyses/<analysis_id>/update/
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def video_analysis_update(request, analysis_id):
    try:
        va = VideoAnalysis.objects.get(pk=analysis_id)
    except VideoAnalysis.DoesNotExist:
        return error_response("Video analysis not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "eye_contact_score" in data:
        va.eye_contact_score = data["eye_contact_score"]
    if "dress_code" in data:
        va.dress_code = data["dress_code"]
    if "dress_score" in data:
        va.dress_score = data["dress_score"]
    if "confidence_score" in data:
        va.confidence_score = data["confidence_score"]
    if "overall_video_score" in data:
        va.overall_video_score = data["overall_video_score"]

    va.save()
    return success_response(
        {"analysis_id": va.analysis_id},
        message="Video analysis updated",
    )


# ============================================================
# DELETE VIDEO ANALYSIS
# DELETE /api/video-analyses/<analysis_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def video_analysis_delete(request, analysis_id):
    try:
        va = VideoAnalysis.objects.get(pk=analysis_id)
    except VideoAnalysis.DoesNotExist:
        return error_response("Video analysis not found", status=404)

    va.delete()
    return success_response(message="Video analysis deleted")