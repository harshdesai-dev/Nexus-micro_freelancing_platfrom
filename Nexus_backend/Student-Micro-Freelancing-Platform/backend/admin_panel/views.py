from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.models import User
from accounts.serializers import user_to_dict
from authentication.views import body, error, role_required, success
from clients.models import Dispute, Job, Report
from students.models import Verification, VerificationHistory
from .models import AdminActionHistory


def audit(actor, entity_type, entity_id, action, details=None):
    AdminActionHistory.objects.create(actor=actor, entity_type=entity_type, entity_id=entity_id, action=action, details=details or {})


@require_http_methods(["GET"])
@role_required("ADMIN")
def manage_students(request):
    return success({"students": [user_to_dict(u) for u in User.objects.filter(role=User.Role.STUDENT).order_by("-created_at")]})


@require_http_methods(["GET"])
@role_required("ADMIN")
def student_detail(request, student_id):
    try: user = User.objects.get(id=student_id, role=User.Role.STUDENT)
    except User.DoesNotExist: return error("NOT_FOUND", "Student not found.", 404)
    return success({"student": user_to_dict(user)})


@csrf_exempt
@require_http_methods(["PATCH"])
@role_required("ADMIN")
def update_student_status(request, student_id):
    data = body(request); status = str(data.get("account_status", "")).upper() if data else ""
    if status not in User.AccountStatus.values: return error("VALIDATION_ERROR", "Invalid account_status.")
    try: user = User.objects.get(id=student_id, role=User.Role.STUDENT)
    except User.DoesNotExist: return error("NOT_FOUND", "Student not found.", 404)
    user.account_status = status; user.save(update_fields=["account_status", "updated_at"])
    audit(request.user, "User", user.id, "UPDATE_ACCOUNT_STATUS", {"account_status": status})
    return success({"student": user_to_dict(user)}, "Student status updated")


@require_http_methods(["GET"])
@role_required("ADMIN")
def manage_verifications(request):
    records = Verification.objects.select_related("student", "reviewed_by").order_by("-created_at")
    return success({"verifications": [{"id": str(v.id), "student": user_to_dict(v.student), "status": v.status, "reviewed_by": user_to_dict(v.reviewed_by) if v.reviewed_by else None, "created_at": v.created_at.isoformat()} for v in records]})


@csrf_exempt
@require_http_methods(["PATCH"])
@role_required("ADMIN")
def update_verification(request, verification_id):
    data = body(request); status = str(data.get("status", "")).upper() if data else ""
    if status not in (Verification.Status.VERIFIED, Verification.Status.REJECTED): return error("VALIDATION_ERROR", "status must be VERIFIED or REJECTED.")
    try:
        with transaction.atomic():
            verification = Verification.objects.select_for_update().get(id=verification_id)
            if verification.status != Verification.Status.PENDING: return error("INVALID_STATE", "Only pending verifications may be reviewed.", 409)
            verification.status = status; verification.reviewed_by = request.user; verification.admin_action = status; verification.reviewed_at = __import__("django.utils.timezone", fromlist=["now"]).now(); verification.save()
            VerificationHistory.objects.create(verification=verification, previous_status=Verification.Status.PENDING, new_status=status, action=f"Verification {status.lower()}", actor=request.user, reason=str(data.get("reason", "")))
            audit(request.user, "Verification", verification.id, "REVIEW_VERIFICATION", {"status": status})
    except Verification.DoesNotExist: return error("NOT_FOUND", "Verification not found.", 404)
    return success({"verification": {"id": str(verification.id), "status": verification.status}}, "Verification reviewed")


@require_http_methods(["GET"])
@role_required("ADMIN")
def verification_history(request, verification_id):
    if not Verification.objects.filter(id=verification_id).exists(): return error("NOT_FOUND", "Verification not found.", 404)
    history = VerificationHistory.objects.filter(verification_id=verification_id).order_by("created_at")
    return success({"history": [{"id": str(h.id), "previous_status": h.previous_status, "new_status": h.new_status, "action": h.action, "created_at": h.created_at.isoformat()} for h in history]})


@require_http_methods(["GET"])
@role_required("ADMIN")
def manage_clients(request):
    return success({"clients": [user_to_dict(u) for u in User.objects.filter(role=User.Role.CLIENT).order_by("-created_at")]})


@require_http_methods(["GET"])
@role_required("ADMIN")
def client_detail(request, client_id):
    try: user = User.objects.get(id=client_id, role=User.Role.CLIENT)
    except User.DoesNotExist: return error("NOT_FOUND", "Client not found.", 404)
    return success({"client": user_to_dict(user)})


@csrf_exempt
@require_http_methods(["PATCH"])
@role_required("ADMIN")
def update_client_status(request, client_id):
    data = body(request); status = str(data.get("account_status", "")).upper() if data else ""
    if status not in User.AccountStatus.values: return error("VALIDATION_ERROR", "Invalid account_status.")
    try: user = User.objects.get(id=client_id, role=User.Role.CLIENT)
    except User.DoesNotExist: return error("NOT_FOUND", "Client not found.", 404)
    user.account_status = status; user.save(update_fields=["account_status", "updated_at"])
    audit(request.user, "User", user.id, "UPDATE_ACCOUNT_STATUS", {"account_status": status})
    return success({"client": user_to_dict(user)}, "Client status updated")


@require_http_methods(["GET"])
@role_required("ADMIN")
def manage_jobs(request):
    jobs = Job.objects.select_related("job_provider", "selected_student").all().order_by("-created_at")
    return success({"jobs": [{"id": str(j.id), "title": j.title, "job_state": j.status, "job_provider": user_to_dict(j.job_provider), "selected_student": user_to_dict(j.selected_student) if j.selected_student else None} for j in jobs]})


@require_http_methods(["GET"])
@role_required("ADMIN")
def job_detail(request, job_id):
    try: job = Job.objects.select_related("job_provider", "selected_student").get(id=job_id)
    except Job.DoesNotExist: return error("NOT_FOUND", "Job not found.", 404)
    return success({"job": {"id": str(job.id), "title": job.title, "description": job.description, "job_state": job.status, "job_provider": user_to_dict(job.job_provider)}})


@csrf_exempt
@require_http_methods(["PATCH"])
@role_required("ADMIN")
def update_job_status(request, job_id):
    data = body(request); status = str(data.get("job_state", "")).upper() if data else ""
    if status not in Job.Status.values: return error("VALIDATION_ERROR", "Invalid job_state.")
    try: job = Job.objects.get(id=job_id)
    except Job.DoesNotExist: return error("NOT_FOUND", "Job not found.", 404)
    job.status = status; job.save(update_fields=["status", "updated_at"])
    audit(request.user, "Job", job.id, "UPDATE_JOB_STATE", {"job_state": status})
    return success({"job": {"id": str(job.id), "job_state": job.status}}, "Job state updated")


@require_http_methods(["GET"])
@role_required("ADMIN")
def manage_reports(request):
    reports = Report.objects.select_related("reporter").order_by("-created_at")
    return success({"reports": [{"id": str(r.id), "status": r.status, "reason": r.reason, "reporter": user_to_dict(r.reporter)} for r in reports]})


@csrf_exempt
@require_http_methods(["PATCH"])
@role_required("ADMIN")
def update_report(request, report_id):
    data = body(request); status = str(data.get("status", "")).upper() if data else ""
    if status not in Report.Status.values: return error("VALIDATION_ERROR", "Invalid report status.")
    try: report = Report.objects.get(id=report_id)
    except Report.DoesNotExist: return error("NOT_FOUND", "Report not found.", 404)
    report.status = status; report.admin_action = str(data.get("admin_action", "")); report.reviewed_by = request.user; report.save()
    audit(request.user, "Report", report.id, "REVIEW_REPORT", {"status": status})
    return success({"report": {"id": str(report.id), "status": report.status}}, "Report updated")


@require_http_methods(["GET"])
@role_required("ADMIN")
def manage_disputes(request):
    disputes = Dispute.objects.select_related("raised_by", "job").order_by("-created_at")
    return success({"disputes": [{"id": str(d.id), "status": d.status, "issue": d.issue, "raised_by": user_to_dict(d.raised_by)} for d in disputes]})


@csrf_exempt
@require_http_methods(["PATCH"])
@role_required("ADMIN")
def update_dispute(request, dispute_id):
    data = body(request); status = str(data.get("status", "")).upper() if data else ""
    if status not in Dispute.Status.values: return error("VALIDATION_ERROR", "Invalid dispute status.")
    try: dispute = Dispute.objects.get(id=dispute_id)
    except Dispute.DoesNotExist: return error("NOT_FOUND", "Dispute not found.", 404)
    dispute.status = status; dispute.admin_handling = str(data.get("admin_handling", dispute.admin_handling)); dispute.resolution = str(data.get("resolution", dispute.resolution)); dispute.reviewed_by = request.user; dispute.save()
    audit(request.user, "Dispute", dispute.id, "REVIEW_DISPUTE", {"status": status})
    return success({"dispute": {"id": str(dispute.id), "status": dispute.status}}, "Dispute updated")
