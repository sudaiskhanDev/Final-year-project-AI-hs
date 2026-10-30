from django.urls import path

from .views.resume_matching_views import (
    resume_matching_create,
    resume_matching_list,
    resume_matching_detail,
    resume_matching_update,
    resume_matching_delete,
)




from .views.ai_interview_views import (
    ai_interview_create,
    ai_interview_list,
    ai_interview_detail,
    ai_interview_update,
    ai_interview_delete,
)






from .views.question_views import (
    question_create,
    question_list,
    question_detail,
    question_update,
    question_delete,
)




from .views.video_analysis_views import (
    video_analysis_create,
    video_analysis_list,
    video_analysis_detail,
    video_analysis_update,
    video_analysis_delete,
)


from .views.hiring_result_views import (
    hiring_result_create,
    hiring_result_list,
    hiring_result_detail,
    hiring_result_update,
    hiring_result_delete,
)


urlpatterns = [
    # Resume Matching
    path("resume-matchings/", resume_matching_list, name="resume-matching-list"),
    path("resume-matchings/create/", resume_matching_create, name="resume-matching-create"),
    path("resume-matchings/<int:matching_id>/", resume_matching_detail, name="resume-matching-detail"),
    path("resume-matchings/<int:matching_id>/update/", resume_matching_update, name="resume-matching-update"),
    path("resume-matchings/<int:matching_id>/delete/", resume_matching_delete, name="resume-matching-delete"),



        # AI Interview
    path("ai-interviews/", ai_interview_list, name="ai-interview-list"),
    path("ai-interviews/create/", ai_interview_create, name="ai-interview-create"),
    path("ai-interviews/<int:interview_id>/", ai_interview_detail, name="ai-interview-detail"),
    path("ai-interviews/<int:interview_id>/update/", ai_interview_update, name="ai-interview-update"),
    path("ai-interviews/<int:interview_id>/delete/", ai_interview_delete, name="ai-interview-delete"),



        # Question
    path("questions/", question_list, name="question-list"),
    path("questions/create/", question_create, name="question-create"),
    path("questions/<int:question_id>/", question_detail, name="question-detail"),
    path("questions/<int:question_id>/update/", question_update, name="question-update"),
    path("questions/<int:question_id>/delete/", question_delete, name="question-delete"),



        # Video Analysis
    path("video-analyses/", video_analysis_list, name="video-analysis-list"),
    path("video-analyses/create/", video_analysis_create, name="video-analysis-create"),
    path("video-analyses/<int:analysis_id>/", video_analysis_detail, name="video-analysis-detail"),
    path("video-analyses/<int:analysis_id>/update/", video_analysis_update, name="video-analysis-update"),
    path("video-analyses/<int:analysis_id>/delete/", video_analysis_delete, name="video-analysis-delete"),





        # Hiring Result
    path("hiring-results/", hiring_result_list, name="hiring-result-list"),
    path("hiring-results/create/", hiring_result_create, name="hiring-result-create"),
    path("hiring-results/<int:result_id>/", hiring_result_detail, name="hiring-result-detail"),
    path("hiring-results/<int:result_id>/update/", hiring_result_update, name="hiring-result-update"),
    path("hiring-results/<int:result_id>/delete/", hiring_result_delete, name="hiring-result-delete"),

]