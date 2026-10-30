from django.urls import path

from .views import (
    generate_question_view,
    parse_cv_view,
    parse_cv_by_resume_id_view,
)


urlpatterns = [
    path("generate-question/", generate_question_view, name="ai-generate-question"),
    path("parse-cv/", parse_cv_view, name="ai-parse-cv"),
    path("parse-cv/<int:resume_id>/", parse_cv_by_resume_id_view, name="ai-parse-cv-by-id"),
]