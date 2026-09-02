from django.urls import path
from . import views

urlpatterns = [
    path("students", views.manage_students),
    path("students/<uuid:student_id>", views.student_detail),
    path("students/<uuid:student_id>/status", views.update_student_status),
    path("clients", views.manage_clients),
    path("clients/<uuid:client_id>", views.client_detail),
    path("clients/<uuid:client_id>/status", views.update_client_status),
    path("verifications", views.manage_verifications),
    path("verifications/<uuid:verification_id>", views.update_verification),
    path("verifications/<uuid:verification_id>/history", views.verification_history),
    path("jobs", views.manage_jobs),
    path("jobs/<uuid:job_id>", views.job_detail),
    path("jobs/<uuid:job_id>/status", views.update_job_status),
    path("reports", views.manage_reports),
    path("reports/<uuid:report_id>", views.update_report),
    path("disputes", views.manage_disputes),
    path("disputes/<uuid:dispute_id>", views.update_dispute),
]
