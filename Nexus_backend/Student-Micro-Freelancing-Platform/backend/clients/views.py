from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.models import User
from accounts.serializers import user_to_dict
from authentication.views import body, error, jwt_required, role_required, success
from students.models import StudentProfile
from .models import Application, ClientProfile, Dispute, Job, Message, Payment, Rating, Report, Submission


def _timestamp(value):
    return value.isoformat() if value else None


def job_data(job):
    return {
        "id": str(job.id), "title": job.title, "description": job.description,
        "required_skills": job.required_skills, "budget": str(job.budget),
        "deadline": _timestamp(job.deadline), "reference_files": job.reference_files,
        "job_provider": user_to_dict(job.job_provider),
        "selected_student": user_to_dict(job.selected_student) if job.selected_student else None,
        "job_state": job.status, "created_at": _timestamp(job.created_at), "updated_at": _timestamp(job.updated_at),
    }


def application_data(application):
    job = application.job
    return {
        "id": str(application.id),
        "status": application.status,
        "application_information": application.application_information,
        "application_message": application.application_message,
        "expected_completion": application.expected_completion.isoformat() if application.expected_completion else None,
        "created_at": _timestamp(application.created_at),
        "updated_at": _timestamp(application.updated_at),
        "job": {
            "id": str(job.id), "title": job.title, "budget": str(job.budget),
            "deadline": _timestamp(job.deadline), "job_state": job.status,
            "job_provider": user_to_dict(job.job_provider),
        },
    }


def submission_data(submission):
    return {"id": str(submission.id), "job": str(submission.job_id), "student": str(submission.student_id), "submitted_work": submission.submitted_work, "submission_information": submission.submission_information, "status": submission.submission_status, "created_at": _timestamp(submission.created_at), "updated_at": _timestamp(submission.updated_at)}


def _job_or_error(job_id):
    try:
        return Job.objects.select_related("job_provider", "selected_student").get(id=job_id)
    except Job.DoesNotExist:
        return None


def _participant(job, user):
    return job.job_provider_id == user.id or job.selected_student_id == user.id


@csrf_exempt
@require_http_methods(["GET", "PATCH"])
@jwt_required
def profile_me(request):
    if request.user.role == User.Role.STUDENT:
        profile, _ = StudentProfile.objects.get_or_create(user=request.user)
        if request.method == "PATCH":
            data = body(request)
            if data is None: return error("INVALID_JSON", "Invalid JSON in request body.")
            allowed = ("college", "course", "year_of_study", "bio", "availability", "skills_data", "portfolio", "previous_work", "profile_information")
            for field in allowed:
                if field in data: setattr(profile, field, data[field])
            profile.full_clean(); profile.save()
        return success({"role": "STUDENT", "profile": {"user_id": str(profile.user_id), "college": profile.college, "course": profile.course, "year_of_study": profile.year_of_study, "bio": profile.bio, "availability": profile.availability, "skills": profile.skills_data, "portfolio": profile.portfolio, "previous_work": profile.previous_work, "profile_information": profile.profile_information}})
    if request.user.role == User.Role.CLIENT:
        profile, _ = ClientProfile.objects.get_or_create(user=request.user)
        if request.method == "PATCH":
            data = body(request)
            if data is None: return error("INVALID_JSON", "Invalid JSON in request body.")
            if "profile_information" in data: profile.profile_information = data["profile_information"]
            if "reputation" in data: profile.reputation = data["reputation"]
            profile.full_clean(); profile.save()
        return success({"role": "CLIENT", "profile": {"user_id": str(profile.user_id), "profile_information": profile.profile_information, "reputation": str(profile.reputation)}})
    return error("FORBIDDEN", "Administrators do not have a marketplace profile.", 403)


@csrf_exempt
@require_http_methods(["GET", "POST"])
@jwt_required
def jobs_view(request):
    if request.method == "GET":
        jobs = Job.objects.select_related("job_provider", "selected_student").filter(status__in=[Job.Status.POSTED, Job.Status.APPLICATIONS]).order_by("-created_at")
        return success({"jobs": [job_data(job) for job in jobs]})
    if request.user.role not in (User.Role.STUDENT, User.Role.CLIENT):
        return error("FORBIDDEN", "Only STUDENT or CLIENT users may create jobs.", 403)
    data = body(request)
    if data is None: return error("INVALID_JSON", "Invalid JSON in request body.")
    missing = [field for field in ("title", "description", "budget") if not data.get(field)]
    if missing: return error("VALIDATION_ERROR", f"Missing required fields: {', '.join(missing)}.")
    try: budget = Decimal(str(data["budget"]))
    except (InvalidOperation, ValueError): return error("VALIDATION_ERROR", "budget must be a valid number.")
    deadline = parse_datetime(data["deadline"]) if data.get("deadline") else None
    if data.get("deadline") and deadline is None: return error("VALIDATION_ERROR", "deadline must be ISO-8601 datetime.")
    job = Job(title=data["title"], description=data["description"], required_skills=data.get("required_skills", []), budget=budget, deadline=deadline, reference_files=data.get("reference_files", []), job_provider=request.user)
    try: job.full_clean(); job.save()
    except Exception: return error("VALIDATION_ERROR", "Invalid job data.")
    return success({"job": job_data(job)}, "Job created", 201)


@require_http_methods(["GET"])
@jwt_required
def job_detail_view(request, job_id):
    job = _job_or_error(job_id)
    if not job: return error("NOT_FOUND", "Job not found.", 404)
    return success({"job": job_data(job)})


@csrf_exempt
@require_http_methods(["GET", "POST"])
@jwt_required
def applications_view(request, job_id):
    job = _job_or_error(job_id)
    if not job: return error("NOT_FOUND", "Job not found.", 404)
    if request.method == "GET":
        if job.job_provider_id != request.user.id: return error("FORBIDDEN", "Only the job provider may view applications.", 403)
        apps = Application.objects.select_related("student").filter(job=job).order_by("-created_at")
        return success({"applications": [{"id": str(a.id), "student": user_to_dict(a.student), "application_information": a.application_information, "status": a.status, "created_at": _timestamp(a.created_at)} for a in apps]})
    if request.user.role != User.Role.STUDENT: return error("FORBIDDEN", "Only STUDENT users may apply.", 403)
    if job.status not in (Job.Status.POSTED, Job.Status.APPLICATIONS): return error("INVALID_STATE", "This job is not accepting applications.", 409)
    if job.job_provider_id == request.user.id: return error("FORBIDDEN", "A provider cannot apply to their own job.", 403)
    data = body(request)
    if data is None: return error("INVALID_JSON", "Invalid JSON in request body.")
    try:
        with transaction.atomic():
            application = Application.objects.create(job=job, student=request.user, application_information=data.get("application_information", {}), application_message=str(data.get("application_message", "")), expected_completion=data.get("expected_completion") or None)
            if job.status == Job.Status.POSTED:
                job.status = Job.Status.APPLICATIONS; job.save(update_fields=["status", "updated_at"])
    except IntegrityError: return error("APPLICATION_EXISTS", "You have already applied to this job.", 409)
    return success({"application": {"id": str(application.id), "status": application.status}}, "Application submitted", 201)


@require_http_methods(["GET"])
@role_required("STUDENT")
def my_applications_view(request):
    applications = Application.objects.select_related("job", "job__job_provider").filter(student=request.user).order_by("-created_at")
    return success({"applications": [application_data(application) for application in applications]})


@require_http_methods(["GET"])
@role_required("STUDENT")
def application_detail_view(request, application_id):
    try:
        application = Application.objects.select_related("job", "job__job_provider").get(id=application_id, student=request.user)
    except Application.DoesNotExist:
        return error("NOT_FOUND", "Application not found.", 404)
    return success({"application": application_data(application)})


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def select_view(request, job_id):
    data = body(request)
    if data is None or not data.get("application_id"): return error("VALIDATION_ERROR", "application_id is required.")
    try:
        with transaction.atomic():
            job = Job.objects.select_for_update().select_related("job_provider").get(id=job_id)
            if job.job_provider_id != request.user.id: return error("FORBIDDEN", "Only the job provider may select a student.", 403)
            if job.status not in (Job.Status.POSTED, Job.Status.APPLICATIONS): return error("INVALID_STATE", "This job cannot select a student now.", 409)
            application = Application.objects.select_for_update().select_related("student").get(id=data["application_id"], job=job)
            if application.status != Application.Status.APPLIED or application.student.role != User.Role.STUDENT: return error("INVALID_APPLICATION", "Application is not eligible for selection.", 409)
            if Application.objects.filter(job=job, status=Application.Status.SELECTED).exists(): return error("STUDENT_ALREADY_SELECTED", "A student is already selected.", 409)
            application.status = Application.Status.SELECTED; application.save(update_fields=["status", "updated_at"])
            job.selected_student = application.student; job.status = Job.Status.STUDENT_SELECTED; job.save(update_fields=["selected_student", "status", "updated_at"])
    except (Job.DoesNotExist, Application.DoesNotExist): return error("NOT_FOUND", "Job or application not found.", 404)
    return success({"job": job_data(job)}, "Student selected")


@csrf_exempt
@require_http_methods(["GET", "POST"])
@jwt_required
def messages_view(request, job_id):
    job = _job_or_error(job_id)
    if not job: return error("NOT_FOUND", "Job not found.", 404)
    if not job.selected_student_id: return error("INVALID_STATE", "Messaging starts after student selection.", 409)
    if not _participant(job, request.user): return error("FORBIDDEN", "Only selected job participants may communicate.", 403)
    if request.method == "GET":
        messages = Message.objects.select_related("sender").filter(job=job).order_by("timestamp")
        return success({"messages": [{"id": str(m.id), "sender": user_to_dict(m.sender), "message": m.message, "timestamp": _timestamp(m.timestamp)} for m in messages]})
    data = body(request); text = str(data.get("message", "")).strip() if data else ""
    if not text: return error("VALIDATION_ERROR", "message cannot be blank.")
    message = Message.objects.create(job=job, sender=request.user, message=text)
    if job.status == Job.Status.STUDENT_SELECTED: job.status = Job.Status.IN_PROGRESS; job.save(update_fields=["status", "updated_at"])
    return success({"message": {"id": str(message.id), "timestamp": _timestamp(message.timestamp)}}, "Message sent", 201)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def submissions_view(request, job_id):
    job = _job_or_error(job_id)
    if not job: return error("NOT_FOUND", "Job not found.", 404)
    if job.selected_student_id != request.user.id: return error("FORBIDDEN", "Only the selected student may submit work.", 403)
    if job.status not in (Job.Status.STUDENT_SELECTED, Job.Status.IN_PROGRESS, Job.Status.WORK_SUBMITTED): return error("INVALID_STATE", "Work cannot be submitted in the current job state.", 409)
    data = body(request)
    if data is None: return error("INVALID_JSON", "Invalid JSON in request body.")
    submission = Submission.objects.create(job=job, student=request.user, submitted_work=data.get("submitted_work", []), submission_information=data.get("submission_information", {}))
    job.status = Job.Status.WORK_SUBMITTED; job.save(update_fields=["status", "updated_at"])
    return success({"submission": submission_data(submission)}, "Work submitted", 201)


@csrf_exempt
@require_http_methods(["GET", "PATCH"])
@jwt_required
def submission_review_view(request, job_id, submission_id):
    job = _job_or_error(job_id)
    if not job: return error("NOT_FOUND", "Job not found.", 404)
    try: submission = Submission.objects.get(id=submission_id, job=job)
    except Submission.DoesNotExist: return error("NOT_FOUND", "Submission not found.", 404)
    if job.job_provider_id != request.user.id: return error("FORBIDDEN", "Only the job provider may review submissions.", 403)
    if request.method == "GET": return success({"submission": submission_data(submission)})
    data = body(request); action = str(data.get("status", "")).upper() if data else ""
    if action not in (Submission.Status.ACCEPTED, Submission.Status.REJECTED): return error("VALIDATION_ERROR", "status must be ACCEPTED or REJECTED.")
    submission.submission_status = action; submission.save(update_fields=["submission_status", "updated_at"])
    if action == Submission.Status.ACCEPTED:
        job.status = Job.Status.PAYMENT; job.save(update_fields=["status", "updated_at"])
    else:
        job.status = Job.Status.IN_PROGRESS; job.save(update_fields=["status", "updated_at"])
    return success({"submission": submission_data(submission)}, "Submission reviewed")


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def payment_view(request, job_id):
    job = _job_or_error(job_id)
    if not job: return error("NOT_FOUND", "Job not found.", 404)
    if job.job_provider_id != request.user.id: return error("FORBIDDEN", "Only the job provider may create a payment.", 403)
    if job.status != Job.Status.PAYMENT: return error("INVALID_STATE", "Payment requires an accepted submission.", 409)
    data = body(request)
    if data is None: return error("INVALID_JSON", "Invalid JSON in request body.")
    try: amount = Decimal(str(data.get("amount", job.budget))); commission = Decimal(str(data.get("platform_commission", 0)))
    except (InvalidOperation, ValueError): return error("VALIDATION_ERROR", "amount and platform_commission must be valid numbers.")
    state = str(data.get("transaction_state", Payment.Status.PENDING)).upper()
    if state != Payment.Status.PENDING: return error("PAYMENT_GATEWAY_REQUIRED", "Only PENDING payments may be created until gateway verification is implemented.", 409)
    payment = Payment(job=job, payer=request.user, recipient=job.selected_student, amount=amount, platform_commission=commission, transaction_status=state, transaction_reference=data.get("transaction_reference") or None)
    try: payment.full_clean(); payment.save()
    except Exception: return error("VALIDATION_ERROR", "Invalid payment data.")
    return success({"payment": {"id": str(payment.id), "transaction_state": payment.transaction_status}}, "Payment recorded", 201)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def ratings_view(request, job_id):
    job = _job_or_error(job_id)
    if not job: return error("NOT_FOUND", "Job not found.", 404)
    if job.status not in (Job.Status.COMPLETED, Job.Status.RATED): return error("INVALID_STATE", "Ratings are available only after completed payment.", 409)
    if not _participant(job, request.user): return error("FORBIDDEN", "Only job participants may rate.", 403)
    data = body(request)
    if data is None: return error("INVALID_JSON", "Invalid JSON in request body.")
    reviewed_id = data.get("reviewed_user_id")
    try: reviewed = User.objects.get(id=reviewed_id); rating_value = int(data.get("rating"))
    except (User.DoesNotExist, TypeError, ValueError): return error("VALIDATION_ERROR", "A valid reviewed_user_id and rating are required.")
    if reviewed.id == request.user.id or not _participant(job, reviewed): return error("VALIDATION_ERROR", "Ratings must be for the other job participant.")
    try:
        rating = Rating(job=job, reviewer=request.user, reviewed_user=reviewed, rating=rating_value, review_content=str(data.get("review_content", "")))
        rating.full_clean(); rating.save()
    except Exception: return error("VALIDATION_ERROR", "Invalid or duplicate rating data.")
    job.status = Job.Status.RATED; job.save(update_fields=["status", "updated_at"])
    return success({"rating": {"id": str(rating.id), "rating": rating.rating}}, "Rating submitted", 201)


@csrf_exempt
@require_http_methods(["GET", "POST"])
@jwt_required
def reports_view(request):
    if request.method == "GET":
        reports = Report.objects.filter(reporter=request.user).order_by("-created_at")
        return success({"reports": [{"id": str(report.id), "status": report.status, "reason": report.reason, "details": report.details} for report in reports]})
    data = body(request)
    if data is None: return error("INVALID_JSON", "Invalid JSON in request body.")
    try:
        reported_user = User.objects.filter(id=data.get("reported_user_id")).first() if data.get("reported_user_id") else None
        reported_job = Job.objects.filter(id=data.get("reported_job_id")).first() if data.get("reported_job_id") else None
        related_job = Job.objects.filter(id=data.get("related_job_id")).first() if data.get("related_job_id") else None
    except (ValueError, TypeError): return error("VALIDATION_ERROR", "Invalid report target identifier.")
    if not any((reported_user, reported_job, related_job)) or not data.get("reason") or not data.get("details"): return error("VALIDATION_ERROR", "reason, details, and at least one valid target are required.")
    report = Report.objects.create(reporter=request.user, reported_user=reported_user, reported_job=reported_job, related_job=related_job, reason=str(data["reason"]), details=str(data["details"]))
    return success({"report": {"id": str(report.id), "status": report.status}}, "Report submitted", 201)


@csrf_exempt
@require_http_methods(["GET", "POST"])
@jwt_required
def disputes_view(request, job_id):
    job = _job_or_error(job_id)
    if not job: return error("NOT_FOUND", "Job not found.", 404)
    if not job.selected_student_id: return error("INVALID_STATE", "Disputes require a selected job participant.", 409)
    if not _participant(job, request.user): return error("FORBIDDEN", "Only job participants may access disputes.", 403)
    if request.method == "GET":
        disputes = Dispute.objects.filter(job=job)
        return success({"disputes": [{"id": str(d.id), "issue": d.issue, "details": d.details, "status": d.status} for d in disputes]})
    data = body(request)
    if data is None or not data.get("issue") or not data.get("details"): return error("VALIDATION_ERROR", "issue and details are required.")
    dispute = Dispute.objects.create(job=job, raised_by=request.user, issue=str(data["issue"]), details=str(data["details"]))
    dispute.involved_users.add(job.job_provider, job.selected_student)
    return success({"dispute": {"id": str(dispute.id), "status": dispute.status}}, "Dispute raised", 201)
