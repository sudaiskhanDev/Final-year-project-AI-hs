from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.hiring.models import AIInterview, Question
from utils.response import success_response, error_response
from utils.validators import parse_json, require_fields


# ============================================================
# CREATE QUESTION
# POST /api/questions/create/
# Body: { interview_id, question_text, answer_text?, answer_score?, time_taken? }
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def question_create(request):
    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    err = require_fields(data, ["interview_id", "question_text"])
    if err:
        return error_response(err, status=400)

    try:
        interview = AIInterview.objects.get(pk=data["interview_id"])
    except AIInterview.DoesNotExist:
        return error_response("Interview not found", status=404)

    q = Question.objects.create(
        interview=interview,
        question_text=data["question_text"],
        answer_text=data.get("answer_text"),
        answer_score=data.get("answer_score", 0),
        time_taken=data.get("time_taken", 0),
    )

    return success_response(
        {
            "question_id": q.question_id,
            "interview_id": q.interview.interview_id,
            "question_text": q.question_text,
            "answer_text": q.answer_text,
            "answer_score": str(q.answer_score),
            "time_taken": q.time_taken,
        },
        message="Question created",
        status=201,
    )


# ============================================================
# LIST QUESTIONS
# GET /api/questions/
# ============================================================
@require_http_methods(["GET"])
def question_list(request):
    items = list(
        Question.objects.select_related("interview").values(
            "question_id",
            "interview_id",
            "question_text",
            "answer_text",
            "answer_score",
            "time_taken",
        )
    )
    for item in items:
        item["answer_score"] = str(item["answer_score"])
    return success_response(items, message="Questions fetched")


# ============================================================
# GET ONE QUESTION
# GET /api/questions/<question_id>/
# ============================================================
@require_http_methods(["GET"])
def question_detail(request, question_id):
    try:
        q = Question.objects.select_related(
            "interview__application__candidate__user",
            "interview__application__job",
        ).get(pk=question_id)
    except Question.DoesNotExist:
        return error_response("Question not found", status=404)

    return success_response({
        "question_id": q.question_id,
        "interview_id": q.interview.interview_id,
        "candidate_name": q.interview.application.candidate.user.full_name,
        "job_title": q.interview.application.job.job_title,
        "question_text": q.question_text,
        "answer_text": q.answer_text,
        "answer_score": str(q.answer_score),
        "time_taken": q.time_taken,
    }, message="Question fetched")


# ============================================================
# UPDATE QUESTION
# PUT /api/questions/<question_id>/update/
# ============================================================
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def question_update(request, question_id):
    try:
        q = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return error_response("Question not found", status=404)

    data, err = parse_json(request)
    if err:
        return error_response(err, status=400)

    if "question_text" in data:
        q.question_text = data["question_text"]
    if "answer_text" in data:
        q.answer_text = data["answer_text"]
    if "answer_score" in data:
        q.answer_score = data["answer_score"]
    if "time_taken" in data:
        q.time_taken = data["time_taken"]

    q.save()
    return success_response(
        {"question_id": q.question_id},
        message="Question updated",
    )


# ============================================================
# DELETE QUESTION
# DELETE /api/questions/<question_id>/delete/
# ============================================================
@csrf_exempt
@require_http_methods(["DELETE"])
def question_delete(request, question_id):
    try:
        q = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return error_response("Question not found", status=404)

    q.delete()
    return success_response(message="Question deleted")