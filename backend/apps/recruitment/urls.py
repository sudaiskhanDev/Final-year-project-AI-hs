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




from .views.job_qualification_views import (
    job_qualification_create,
    job_qualification_list,
    job_qualification_detail,
    job_qualification_update,
    job_qualification_delete,
)



from .views.application_views import (
    application_create,
    application_list,
    application_detail,
    application_update,
    application_delete,
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



        # JobQualification
    path("job-qualifications/", job_qualification_list, name="job-qual-list"),
    path("job-qualifications/create/", job_qualification_create, name="job-qual-create"),
    path("job-qualifications/<int:job_qualification_id>/", job_qualification_detail, name="job-qual-detail"),
    path("job-qualifications/<int:job_qualification_id>/update/", job_qualification_update, name="job-qual-update"),
    path("job-qualifications/<int:job_qualification_id>/delete/", job_qualification_delete, name="job-qual-delete"),





        # Application
    path("applications/", application_list, name="application-list"),
    path("applications/create/", application_create, name="application-create"),
    path("applications/<int:application_id>/", application_detail, name="application-detail"),
    path("applications/<int:application_id>/update/", application_update, name="application-update"),
    path("applications/<int:application_id>/delete/", application_delete, name="application-delete"),



    
]