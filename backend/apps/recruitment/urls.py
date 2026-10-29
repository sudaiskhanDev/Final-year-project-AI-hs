from django.urls import path

from .views.jobs_views import (
    job_create,
    job_list,
    job_detail,
    job_update,
    job_delete,
)


urlpatterns = [
    # Jobs
    path("jobs/", job_list, name="job-list"),
    path("jobs/create/", job_create, name="job-create"),
    path("jobs/<int:job_id>/", job_detail, name="job-detail"),
    path("jobs/<int:job_id>/update/", job_update, name="job-update"),
    path("jobs/<int:job_id>/delete/", job_delete, name="job-delete"),
]