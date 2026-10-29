from django.urls import path

from .views import (
    skill_list_create, skill_detail,
    qualification_list_create, qualification_detail,
    language_list_create, language_detail,
)


urlpatterns = [
    # Skills
    path("skills/", skill_list_create, name="skill-list-create"),
    path("skills/<int:skill_id>/", skill_detail, name="skill-detail"),

    # Qualifications
    path("qualifications/", qualification_list_create, name="qualification-list-create"),
    path("qualifications/<int:qualification_id>/", qualification_detail, name="qualification-detail"),

    # Languages
    path("languages/", language_list_create, name="language-list-create"),
    path("languages/<int:lang_id>/", language_detail, name="language-detail"),
]