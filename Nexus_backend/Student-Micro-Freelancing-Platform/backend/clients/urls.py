from django.urls import path
from . import views

urlpatterns = [
    path("profiles/me", views.profile_me),
    path("jobs", views.jobs_view),
    path("jobs/<uuid:job_id>", views.job_detail_view),
    path("jobs/<uuid:job_id>/applications", views.applications_view),
    path("applications/mine", views.my_applications_view),
    path("applications/<uuid:application_id>", views.application_detail_view),
    path("jobs/<uuid:job_id>/select", views.select_view),
    path("jobs/<uuid:job_id>/messages", views.messages_view),
    path("jobs/<uuid:job_id>/submissions", views.submissions_view),
    path("jobs/<uuid:job_id>/submissions/<uuid:submission_id>", views.submission_review_view),
    path("jobs/<uuid:job_id>/payment", views.payment_view),
    path("jobs/<uuid:job_id>/ratings", views.ratings_view),
    path("jobs/<uuid:job_id>/disputes", views.disputes_view),
    path("reports", views.reports_view),
]
