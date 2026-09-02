from django.urls import path
from . import views

urlpatterns = [
    path("review-analysis", views.review_analysis_view, name="review-analysis"),
    path("match-candidates", views.match_candidates_view, name="match-candidates"),
    path("job-recommendations", views.job_recommendations_view, name="job-recommendations"),
    path("profile-improvement", views.profile_improvement_view, name="profile-improvement"),
    path("skill-suggestions", views.skill_suggestions_view, name="skill-suggestions"),
]


