import logging

from django.db.models import Q

from accounts.models import User
from clients.models import Application, Job, Rating
from students.models import StudentProfile
from .gemini_client import (
    analyze_reviews_with_gemini,
    improve_profile_with_gemini,
    match_candidates_with_gemini,
    recommend_jobs_with_gemini,
    suggest_skills_with_gemini,
)

logger = logging.getLogger(__name__)


# =====================================================================
# 1. REVIEW ANALYSIS SERVICE
# =====================================================================

def get_review_analysis(user_id=None, job_id=None, requesting_user=None):
    """
    Retrieve real Rating records from the database and generate an advisory AI review analysis.
    Enforces object-level authorization: reviewed user, relevant job participants, or admin only.
    This service is strictly read-only and never modifies database records.
    """
    target_user = None
    target_job = None

    if user_id:
        try:
            target_user = User.objects.filter(id=user_id).first()
        except Exception:
            return None, "INVALID_USER_ID"
        if not target_user:
            return None, "USER_NOT_FOUND"

    if job_id:
        try:
            target_job = Job.objects.filter(id=job_id).first()
        except Exception:
            return None, "INVALID_JOB_ID"
        if not target_job:
            return None, "JOB_NOT_FOUND"

    if target_job and not target_user:
        ratings_qs = Rating.objects.filter(job=target_job).select_related("reviewer", "reviewed_user", "job")
        target_user = target_job.selected_student or target_job.job_provider
    elif target_user:
        ratings_qs = Rating.objects.filter(reviewed_user=target_user).select_related("reviewer", "job")
        if target_job:
            ratings_qs = ratings_qs.filter(job=target_job)
    else:
        return None, "MISSING_TARGET"

    # Object-level authorization check
    if requesting_user and requesting_user.role != User.Role.ADMIN:
        is_authorized = False
        if target_user and requesting_user.id == target_user.id:
            is_authorized = True
        elif target_job:
            # Job-scoped review analysis is limited to the actual marketplace parties.
            # A mere applicant is not authorized to inspect reviews for other users on the job.
            is_job_provider = requesting_user.id == target_job.job_provider_id
            is_selected_student = requesting_user.id == target_job.selected_student_id

            if not target_user:
                is_authorized = is_job_provider or is_selected_student
            elif is_job_provider and target_user.id == target_job.selected_student_id:
                is_authorized = True
            elif is_selected_student and target_user.id == target_job.job_provider_id:
                is_authorized = True
        elif target_user:
            has_rating = Rating.objects.filter(
                Q(reviewer=requesting_user, reviewed_user=target_user) | Q(reviewer=target_user, reviewed_user=requesting_user)
            ).exists()
            has_shared_job = Job.objects.filter(
                Q(job_provider=requesting_user, selected_student=target_user) | Q(job_provider=target_user, selected_student=requesting_user)
            ).exists()
            if has_rating or has_shared_job:
                is_authorized = True

        if not is_authorized:
            return None, "FORBIDDEN"


    ratings = list(ratings_qs.order_by("-created_at"))
    total_reviews = len(ratings)

    reviews_data = []
    for r in ratings:
        reviews_data.append({
            "id": str(r.id),
            "rating": r.rating,
            "review_content": r.review_content,
            "reviewer_username": r.reviewer.username if r.reviewer else "Anonymous",
            "reviewer_role": r.reviewer.role if r.reviewer else "UNKNOWN",
            "job_title": r.job.title if r.job else "Freelance Project",
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    avg_rating = sum(r.rating for r in ratings) / total_reviews if total_reviews > 0 else 0.0

    user_context = {
        "username": target_user.username if target_user else "User",
        "name": target_user.name if target_user else "",
        "role": target_user.role if target_user else "STUDENT",
        "total_reviews": total_reviews,
        "average_rating": round(avg_rating, 2),
    }

    analysis_output = analyze_reviews_with_gemini(reviews_data, user_context)

    return {
        "target_user": {
            "id": str(target_user.id) if target_user else None,
            "username": target_user.username if target_user else None,
            "name": target_user.name if target_user else None,
            "role": target_user.role if target_user else None,
        } if target_user else None,
        "job_id": str(target_job.id) if target_job else None,
        "total_reviews": total_reviews,
        "average_rating": round(avg_rating, 2),
        "reviews": reviews_data[:10],
        "analysis": analysis_output,
        "is_advisory": True,
    }, None


# =====================================================================
# 2. CANDIDATE MATCHING SERVICE
# =====================================================================

def match_candidates_for_job(job_id, requesting_user):
    """
    Retrieve real Job and Student records to generate advisory candidate recommendations.
    Advisory only: does NOT select, hire, or modify any database record.
    """
    try:
        job = Job.objects.select_related("job_provider", "selected_student").filter(id=job_id).first()
    except Exception:
        return None, "INVALID_JOB_ID"

    if not job:
        return None, "JOB_NOT_FOUND"

    if requesting_user.role != User.Role.ADMIN and job.job_provider_id != requesting_user.id:
        return None, "FORBIDDEN"

    applications = Application.objects.filter(job=job).select_related("student")
    applied_map = {app.student_id: app for app in applications}

    students_qs = (
        User.objects.filter(role=User.Role.STUDENT, account_status=User.AccountStatus.ACTIVE)
        .prefetch_related("student_profile", "student_profile__skills", "portfolio_items")
    )

    all_students = list(students_qs)
    job_skills_lower = [str(s).strip().lower() for s in (job.required_skills or []) if s]

    def candidate_priority(student):
        has_applied = student.id in applied_map
        profile = getattr(student, "student_profile", None)
        skills = []
        if profile and isinstance(profile.skills_data, list):
            skills = [str(s).strip().lower() for s in profile.skills_data if s]
        matched_count = sum(1 for s in skills if any(req in s or s in req for req in job_skills_lower))
        return (1 if has_applied else 0, matched_count)

    sorted_students = sorted(all_students, key=candidate_priority, reverse=True)[:20]

    candidates_data = []
    for student in sorted_students:
        profile = getattr(student, "student_profile", None)
        skills_list = []
        if profile:
            if isinstance(profile.skills_data, list):
                skills_list.extend(profile.skills_data)
            try:
                for sk in profile.skills.all():
                    if sk.name not in skills_list:
                        skills_list.append(sk.name)
            except Exception:
                pass

        portfolio_items = [
            {
                "title": p.title,
                "description": p.description,
                "skills": p.skills,
            }
            for p in student.portfolio_items.filter(is_visible=True)[:3]
        ]

        app = applied_map.get(student.id)

        candidates_data.append({
            "student_id": str(student.id),
            "student_name": student.name or student.username,
            "username": student.username,
            "college": profile.college if profile else "",
            "course": profile.course if profile else "",
            "year_of_study": profile.year_of_study if profile else "",
            "bio": profile.bio if profile else "",
            "availability": profile.availability if profile else "",
            "skills": skills_list,
            "portfolio_items": portfolio_items,
            "has_applied": bool(app),
            "application_message": app.application_message if app else None,
        })

    job_data = {
        "id": str(job.id),
        "title": job.title,
        "description": job.description,
        "required_skills": job.required_skills or [],
        "budget": str(job.budget),
        "deadline": job.deadline.isoformat() if job.deadline else None,
        "status": job.status,
    }

    matching_result = match_candidates_with_gemini(job_data, candidates_data)

    return {
        "job": {
            "id": str(job.id),
            "title": job.title,
            "required_skills": job.required_skills or [],
            "budget": str(job.budget),
            "job_state": job.status,
        },
        "total_candidates_analyzed": len(candidates_data),
        "candidates": matching_result.get("candidates", []),
        "analysis_source": matching_result.get("analysis_source", "SYSTEM_FALLBACK"),
        "is_advisory": True,
    }, None


# =====================================================================
# 3. JOB RECOMMENDATIONS SERVICE
# =====================================================================

def get_job_recommendations_for_student(student_user):
    """
    Retrieve real available Job records and match against the authenticated student's profile.
    Advisory only: does NOT apply to jobs, modify profiles, or mutate any database record.
    """
    if student_user.role != User.Role.STUDENT:
        return None, "NOT_A_STUDENT"

    profile = getattr(student_user, "student_profile", None)
    if not profile:
        profile = StudentProfile.objects.filter(user=student_user).first()

    skills_list = []
    if profile:
        if isinstance(profile.skills_data, list):
            skills_list.extend(profile.skills_data)
        try:
            for sk in profile.skills.all():
                if sk.name not in skills_list:
                    skills_list.append(sk.name)
        except Exception:
            pass

    portfolio_items = [
        {
            "title": p.title,
            "description": p.description,
            "skills": p.skills,
        }
        for p in student_user.portfolio_items.filter(is_visible=True)[:3]
    ]

    student_data = {
        "student_id": str(student_user.id),
        "student_name": student_user.name or student_user.username,
        "username": student_user.username,
        "college": profile.college if profile else "",
        "course": profile.course if profile else "",
        "year_of_study": profile.year_of_study if profile else "",
        "bio": profile.bio if profile else "",
        "availability": profile.availability if profile else "",
        "skills": skills_list,
        "portfolio_items": portfolio_items,
    }

    # Identify jobs the student has already applied to
    applied_job_ids = set(
        Application.objects.filter(student=student_user).values_list("job_id", flat=True)
    )

    # Query active/open jobs excluding already applied jobs and jobs posted by the student
    available_jobs_qs = (
        Job.objects.filter(status__in=[Job.Status.POSTED, Job.Status.APPLICATIONS])
        .exclude(id__in=applied_job_ids)
        .exclude(job_provider=student_user)
        .order_by("-created_at")
    )

    jobs_data = []
    for job in available_jobs_qs[:20]:
        jobs_data.append({
            "id": str(job.id),
            "title": job.title,
            "description": job.description,
            "required_skills": job.required_skills or [],
            "budget": str(job.budget),
            "deadline": job.deadline.isoformat() if job.deadline else None,
            "status": job.status,
        })

    recommendation_result = recommend_jobs_with_gemini(student_data, jobs_data)

    return {
        "student_id": str(student_user.id),
        "total_recommendations": len(recommendation_result.get("recommendations", [])),
        "recommendations": recommendation_result.get("recommendations", []),
        "analysis_source": recommendation_result.get("analysis_source", "SYSTEM_FALLBACK"),
        "is_advisory": True,
    }, None


# =====================================================================
# 4. PROFILE IMPROVEMENT SERVICE
# =====================================================================

def get_profile_improvement_for_student(student_user):
    """
    Retrieve the authenticated student's real profile, skill, and portfolio data,
    and generate advisory AI profile improvement recommendations.
    Advisory only: does NOT modify StudentProfile, User, Skill, PortfolioItem, or any database record.
    """
    if student_user.role != User.Role.STUDENT:
        return None, "NOT_A_STUDENT"

    profile = getattr(student_user, "student_profile", None)
    if not profile:
        profile = StudentProfile.objects.filter(user=student_user).first()

    skills_list = []
    if profile:
        if isinstance(profile.skills_data, list):
            skills_list.extend(profile.skills_data)
        try:
            for sk in profile.skills.all():
                if sk.name not in skills_list:
                    skills_list.append(sk.name)
        except Exception:
            pass

    portfolio_items = [
        {
            "title": p.title,
            "description": p.description,
            "skills": p.skills,
            "project_url": p.project_url,
        }
        for p in student_user.portfolio_items.filter(is_visible=True)[:5]
    ]

    student_data = {
        "student_id": str(student_user.id),
        "student_name": student_user.name or student_user.username,
        "username": student_user.username,
        "college": profile.college if profile else "",
        "course": profile.course if profile else "",
        "year_of_study": profile.year_of_study if profile else "",
        "bio": profile.bio if profile else "",
        "availability": profile.availability if profile else "",
        "skills": skills_list,
        "portfolio_items": portfolio_items,
    }

    improvement_result = improve_profile_with_gemini(student_data)

    return {
        "student_id": str(student_user.id),
        "profile_improvements": improvement_result.get("profile_improvements", []),
        "portfolio_improvements": improvement_result.get("portfolio_improvements", []),
        "skill_presentation": improvement_result.get("skill_presentation", []),
        "missing_information": improvement_result.get("missing_information", []),
        "actionable_recommendations": improvement_result.get("actionable_recommendations", []),
        "analysis_source": improvement_result.get("analysis_source", "SYSTEM_FALLBACK"),
        "is_advisory": True,
    }, None


# =====================================================================
# 5. SKILL SUGGESTIONS SERVICE
# =====================================================================

def get_skill_suggestions_for_student(student_user):
    """
    Retrieve real student profile/skill data and marketplace jobs to suggest relevant new skills.
    Strict business rule: MUST NOT suggest skills the student already possesses.
    Strict security rule: Only student accounts (User.Role.STUDENT) are permitted.
    Advisory only: does NOT modify StudentProfile, Skill, PortfolioItem, or any database record.
    """
    if student_user.role != User.Role.STUDENT:
        return None, "NOT_A_STUDENT"

    profile = getattr(student_user, "student_profile", None)
    if not profile:
        profile = StudentProfile.objects.filter(user=student_user).first()

    skills_list = []
    if profile:
        if isinstance(profile.skills_data, list):
            skills_list.extend(profile.skills_data)
        try:
            for sk in profile.skills.all():
                if sk.name not in skills_list:
                    skills_list.append(sk.name)
        except Exception:
            pass

    existing_skills_lower = {str(s).strip().lower() for s in skills_list if s}

    portfolio_items = [
        {
            "title": p.title,
            "description": p.description,
            "skills": p.skills,
        }
        for p in student_user.portfolio_items.filter(is_visible=True)[:5]
    ]

    student_data = {
        "student_id": str(student_user.id),
        "student_name": student_user.name or student_user.username,
        "username": student_user.username,
        "college": profile.college if profile else "",
        "course": profile.course if profile else "",
        "bio": profile.bio if profile else "",
        "skills": skills_list,
        "portfolio_items": portfolio_items,
    }

    # Fetch active marketplace jobs for marketplace skill demand context
    marketplace_jobs_qs = (
        Job.objects.filter(status__in=[Job.Status.POSTED, Job.Status.APPLICATIONS])
        .order_by("-created_at")[:15]
    )

    marketplace_jobs = [
        {
            "title": j.title,
            "required_skills": j.required_skills or [],
        }
        for j in marketplace_jobs_qs
    ]

    ai_result = suggest_skills_with_gemini(student_data, marketplace_jobs)
    raw_suggestions = ai_result.get("suggestions", [])

    # Mandatory server-side validation & filtering: remove any skills already owned by student
    filtered_suggestions = []
    seen = set()

    for item in raw_suggestions:
        if isinstance(item, dict):
            sk = str(item.get("skill", "")).strip()
            sk_lower = sk.lower()
            if sk and sk_lower not in existing_skills_lower and sk_lower not in seen:
                seen.add(sk_lower)
                filtered_suggestions.append({
                    "skill": sk,
                    "reason": str(item.get("reason", "Useful skill to expand your freelance opportunities.")),
                    "relevance": str(item.get("relevance", "MEDIUM")).upper(),
                    "is_advisory": True,
                })

    return {
        "student_id": str(student_user.id),
        "current_skills": skills_list,
        "suggestions": filtered_suggestions,
        "analysis_source": ai_result.get("analysis_source", "SYSTEM_FALLBACK"),
        "is_advisory": True,
    }, None


