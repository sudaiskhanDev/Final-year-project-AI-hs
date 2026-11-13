from django.urls import path

from .views.apply_job_view import apply_job_view

urlpatterns = [
    path("apply-job/", apply_job_view, name="apply-job"),
]