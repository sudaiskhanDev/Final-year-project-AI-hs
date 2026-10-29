from django.urls import path

from .views.resume_views import (
    resume_create,
    resume_list,
    resume_detail,
    resume_update,
    resume_delete,
)

from .views.cand_experience_views import (
    experience_create,
    experience_list,
    experience_detail,
    experience_update,
    experience_delete,
)




from .views.cand_skill_views import (
    cand_skill_create,
    cand_skill_list,
    cand_skill_detail,
    cand_skill_update,
    cand_skill_delete,
)


from .views.cand_qualification_views import (
    cand_qualification_create,
    cand_qualification_list,
    cand_qualification_detail,
    cand_qualification_update,
    cand_qualification_delete,
)



from .views.cand_language_views import (
    cand_language_create,
    cand_language_list,
    cand_language_detail,
    cand_language_update,
    cand_language_delete,
)





urlpatterns = [
    # Resume
    path("resumes/", resume_list, name="resume-list"),
    path("resumes/create/", resume_create, name="resume-create"),
    path("resumes/<int:resume_id>/", resume_detail, name="resume-detail"),
    path("resumes/<int:resume_id>/update/", resume_update, name="resume-update"),
    path("resumes/<int:resume_id>/delete/", resume_delete, name="resume-delete"),



     # CandExperience
    path("experiences/", experience_list, name="experience-list"),
    path("experiences/create/", experience_create, name="experience-create"),
    path("experiences/<int:exp_id>/", experience_detail, name="experience-detail"),
    path("experiences/<int:exp_id>/update/", experience_update, name="experience-update"),
    path("experiences/<int:exp_id>/delete/", experience_delete, name="experience-delete"),




        # CandidateSkill
    path("candidate-skills/", cand_skill_list, name="cand-skill-list"),
    path("candidate-skills/create/", cand_skill_create, name="cand-skill-create"),
    path("candidate-skills/<int:candidate_skill_id>/", cand_skill_detail, name="cand-skill-detail"),
    path("candidate-skills/<int:candidate_skill_id>/update/", cand_skill_update, name="cand-skill-update"),
    path("candidate-skills/<int:candidate_skill_id>/delete/", cand_skill_delete, name="cand-skill-delete"),



        # CandidateQualification
    path("candidate-qualifications/", cand_qualification_list, name="cand-qual-list"),
    path("candidate-qualifications/create/", cand_qualification_create, name="cand-qual-create"),
    path("candidate-qualifications/<int:cq_id>/", cand_qualification_detail, name="cand-qual-detail"),
    path("candidate-qualifications/<int:cq_id>/update/", cand_qualification_update, name="cand-qual-update"),
    path("candidate-qualifications/<int:cq_id>/delete/", cand_qualification_delete, name="cand-qual-delete"),





        # CandLanguage
    path("candidate-languages/", cand_language_list, name="cand-lang-list"),
    path("candidate-languages/create/", cand_language_create, name="cand-lang-create"),
    path("candidate-languages/<int:cand_lang_id>/", cand_language_detail, name="cand-lang-detail"),
    path("candidate-languages/<int:cand_lang_id>/update/", cand_language_update, name="cand-lang-update"),
    path("candidate-languages/<int:cand_lang_id>/delete/", cand_language_delete, name="cand-lang-delete"),

]