from django.urls import path

from .views.jobs_views import (
    job_create,
    job_list,
    job_detail,
    job_update,
    job_delete,
)



from .views.job_skill_views import (
    job_skill_create,
    job_skill_list,
    job_skill_detail,
    job_skill_update,
    job_skill_delete,
)





urlpatterns = [
    # Jobs
    path("jobs/", job_list, name="job-list"),
    path("jobs/create/", job_create, name="job-create"),
    path("jobs/<int:job_id>/", job_detail, name="job-detail"),
    path("jobs/<int:job_id>/update/", job_update, name="job-update"),
    path("jobs/<int:job_id>/delete/", job_delete, name="job-delete"),




        # JobSkill
    path("job-skills/", job_skill_list, name="job-skill-list"),
    path("job-skills/create/", job_skill_create, name="job-skill-create"),
    path("job-skills/<int:job_skill_id>/", job_skill_detail, name="job-skill-detail"),
    path("job-skills/<int:job_skill_id>/update/", job_skill_update, name="job-skill-update"),
    path("job-skills/<int:job_skill_id>/delete/", job_skill_delete, name="job-skill-delete"),
]