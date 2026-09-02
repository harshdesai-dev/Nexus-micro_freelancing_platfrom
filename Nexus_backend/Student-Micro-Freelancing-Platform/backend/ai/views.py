from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.models import User
from authentication.views import body, error, jwt_required, success
from .services import (
    get_job_recommendations_for_student,
    get_profile_improvement_for_student,
    get_review_analysis,
    get_skill_suggestions_for_student,
    match_candidates_for_job,
)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def review_analysis_view(request):
    """
    POST /api/ai/review-analysis
    Analyzes real marketplace Rating/Review records for a user or job.
    Advisory only; never mutates marketplace state.
    """
    data = body(request)
    if data is None:
        return error("INVALID_JSON", "Invalid JSON in request body.")

    user_id = data.get("user_id") or data.get("student_id")
    job_id = data.get("job_id")

    if not user_id and not job_id:
        user_id = str(request.user.id)

    result, err = get_review_analysis(user_id=user_id, job_id=job_id, requesting_user=request.user)

    if err == "USER_NOT_FOUND":
        return error("NOT_FOUND", "Target user was not found.", 404)
    if err == "INVALID_USER_ID":
        return error("VALIDATION_ERROR", "Invalid user_id format.", 400)
    if err == "JOB_NOT_FOUND":
        return error("NOT_FOUND", "Target job was not found.", 404)
    if err == "INVALID_JOB_ID":
        return error("VALIDATION_ERROR", "Invalid job_id format.", 400)
    if err == "MISSING_TARGET":
        return error("VALIDATION_ERROR", "A valid user_id or job_id is required.", 400)
    if err == "FORBIDDEN":
        return error("FORBIDDEN", "You are not authorized to view review analysis for this user or job.", 403)

    return success(result, "Review analysis generated successfully")


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def match_candidates_view(request):
    """
    POST /api/ai/match-candidates
    Evaluates student candidate fit against job requirements.
    Advisory only; never mutates marketplace state or auto-hires.
    """
    data = body(request)
    if data is None:
        return error("INVALID_JSON", "Invalid JSON in request body.")

    job_id = data.get("job_id")
    if not job_id:
        return error("VALIDATION_ERROR", "job_id is required.", 400)

    result, err = match_candidates_for_job(job_id=job_id, requesting_user=request.user)

    if err == "INVALID_JOB_ID":
        return error("VALIDATION_ERROR", "Invalid job_id format.", 400)
    if err == "JOB_NOT_FOUND":
        return error("NOT_FOUND", "Job not found.", 404)
    if err == "FORBIDDEN":
        return error("FORBIDDEN", "Only the job provider or an administrator may request candidate matching.", 403)

    return success(result, "Candidate matching recommendations generated successfully")


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def job_recommendations_view(request):
    """
    POST /api/ai/job-recommendations
    Recommends open marketplace jobs matching the authenticated student's profile.
    Advisory only; never auto-applies or modifies jobs/profiles.
    """
    if request.user.role != User.Role.STUDENT:
        return error("FORBIDDEN", "Only student accounts may access job recommendations.", 403)

    result, err = get_job_recommendations_for_student(student_user=request.user)

    if err == "NOT_A_STUDENT":
        return error("FORBIDDEN", "Only student accounts may access job recommendations.", 403)

    return success(result, "Job recommendations generated successfully")


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def profile_improvement_view(request):
    """
    POST /api/ai/profile-improvement
    Provides advisory suggestions for improving the authenticated student's profile.
    Advisory only; never modifies student profiles, skills, or portfolio items.
    """
    if request.user.role != User.Role.STUDENT:
        return error("FORBIDDEN", "Only student accounts may access profile improvement suggestions.", 403)

    # Disallow attempting to analyze another student's profile by supplying another student_id in body
    data = body(request)
    if data is not None:
        requested_student_id = data.get("student_id") or data.get("user_id")
        if requested_student_id and str(requested_student_id) != str(request.user.id):
            return error("FORBIDDEN", "You are not authorized to request profile improvement for another student.", 403)

    result, err = get_profile_improvement_for_student(student_user=request.user)

    if err == "NOT_A_STUDENT":
        return error("FORBIDDEN", "Only student accounts may access profile improvement suggestions.", 403)

    return success(result, "Profile improvement suggestions generated successfully")


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def skill_suggestions_view(request):
    """
    POST /api/ai/skill-suggestions
    Provides advisory skill recommendations for the authenticated student.
    Strict authorization: ONLY student accounts (User.Role.STUDENT) are permitted.
    Client and Admin accounts receive 403 FORBIDDEN.
    Advisory only; NEVER creates or modifies Skill or StudentProfile records.
    """
    if request.user.role != User.Role.STUDENT:
        return error("FORBIDDEN", "Only student accounts may access skill suggestions.", 403)

    # Disallow requesting skill suggestions for another student ID
    data = body(request)
    if data is not None:
        requested_student_id = data.get("student_id") or data.get("user_id")
        if requested_student_id and str(requested_student_id) != str(request.user.id):
            return error("FORBIDDEN", "You are not authorized to request skill suggestions for another student.", 403)

    result, err = get_skill_suggestions_for_student(student_user=request.user)

    if err == "NOT_A_STUDENT":
        return error("FORBIDDEN", "Only student accounts may access skill suggestions.", 403)

    return success(result, "Skill suggestions generated successfully")


