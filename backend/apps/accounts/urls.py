from django.urls import path

from .views.auth_views import register, login, logout, me
from .views.user_views import user_list, user_detail, user_update, user_delete

from .views.hr_profile_views import (
    hr_profile_create,
    hr_profile_list,
    hr_profile_detail,
    hr_profile_update,
    hr_profile_delete,
)

from .views.candidate_profile_views import (
    candidate_profile_create,
    candidate_profile_list,
    candidate_profile_detail,
    candidate_profile_update,
    candidate_profile_delete,
)

urlpatterns = [


    # ---------- User CRUD ----------
    path("users/", user_list, name="user-list"),
    path("users/<int:user_id>/", user_detail, name="user-detail"),
    path("users/<int:user_id>/update/", user_update, name="user-update"),
    path("users/<int:user_id>/delete/", user_delete, name="user-delete"),



    # ---------- HR Profile (admin only) ----------
    path("hr-profiles/", hr_profile_list, name="hr-profile-list"),
    path("hr-profiles/create/", hr_profile_create, name="hr-profile-create"),
    path("hr-profiles/<int:hr_id>/", hr_profile_detail, name="hr-profile-detail"),
    path("hr-profiles/<int:hr_id>/update/", hr_profile_update, name="hr-profile-update"),
    path("hr-profiles/<int:hr_id>/delete/", hr_profile_delete, name="hr-profile-delete"),




        # ---------- Candidate Profile ----------
    path("candidate-profiles/", candidate_profile_list, name="candidate-profile-list"),
    path("candidate-profiles/create/", candidate_profile_create, name="candidate-profile-create"),
    path("candidate-profiles/<int:candidate_id>/", candidate_profile_detail, name="candidate-profile-detail"),
    path("candidate-profiles/<int:candidate_id>/update/", candidate_profile_update, name="candidate-profile-update"),
    path("candidate-profiles/<int:candidate_id>/delete/", candidate_profile_delete, name="candidate-profile-delete"),



    # ---------- Auth ----------
    path("auth/register/", register, name="auth-register"),
    path("auth/login/", login, name="auth-login"),
    path("auth/logout/", logout, name="auth-logout"),
    path("auth/me/", me, name="auth-me"),
] 