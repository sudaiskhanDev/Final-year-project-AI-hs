from django.urls import path

from .views.apply_job_view import apply_job_view
from .views.evaluate_application_view import evaluate_application_view


urlpatterns = [
    path("apply-job/", apply_job_view, name="apply-job"),

    # NEW: CV vs Job matching
    path(
        "evaluate-application/<int:application_id>/",
        evaluate_application_view,
        name="evaluate-application",
    ),
    
]