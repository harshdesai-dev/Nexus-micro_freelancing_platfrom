import json
import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)


def get_gemini_api_key():
    """Retrieve Gemini API key from settings or environment."""
    return getattr(settings, "GEMINI_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")


def get_gemini_model():
    """Retrieve configured Gemini model name."""
    return getattr(settings, "GEMINI_MODEL", "") or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


# =====================================================================
# 1. REVIEW ANALYSIS
# =====================================================================

def generate_fallback_analysis(reviews_data, user_context=None):
    """
    Generate a rule-based advisory analysis when Gemini API is offline or unconfigured.
    This guarantees 100% marketplace availability and zero crashes.
    """
    total = len(reviews_data)
    if total == 0:
        return {
            "overall_sentiment": "NO_REVIEWS",
            "sentiment_score": 0.0,
            "summary": "No verified ratings or client reviews have been recorded yet.",
            "strengths": [],
            "improvement_areas": [],
            "recurring_themes": [],
            "advisory_recommendations": [
                "Complete freelance tasks to build reputation and collect verified reviews."
            ],
            "analysis_source": "SYSTEM_FALLBACK",
        }

    ratings = [r.get("rating", 5) for r in reviews_data]
    avg_score = sum(ratings) / total

    if avg_score >= 4.0:
        sentiment = "POSITIVE"
    elif avg_score >= 3.0:
        sentiment = "NEUTRAL"
    elif avg_score >= 2.0:
        sentiment = "MIXED"
    else:
        sentiment = "NEGATIVE"

    contents = [str(r.get("review_content", "")).strip() for r in reviews_data if r.get("review_content")]
    all_text = " ".join(contents).lower()

    strengths = []
    if "quick" in all_text or "time" in all_text or "fast" in all_text:
        strengths.append("Prompt communication and timely delivery")
    if "quality" in all_text or "great" in all_text or "good" in all_text or "excellent" in all_text:
        strengths.append("High quality execution meeting project expectations")
    if not strengths and avg_score >= 3.5:
        strengths.append("Consistent performance across delivered milestones")

    improvement_areas = []
    if "late" in all_text or "delay" in all_text:
        improvement_areas.append("Managing delivery timelines proactively")
    if "communication" in all_text or "response" in all_text:
        improvement_areas.append("Maintaining regular communication updates")
    if not improvement_areas and avg_score < 4.0:
        improvement_areas.append("Enhance clarity and detail in milestone submissions")

    recommendations = [
        "Continue maintaining clear and frequent communication during project milestones.",
        "Highlight verified positive feedback in your student profile bio and portfolio.",
    ]

    return {
        "overall_sentiment": sentiment,
        "sentiment_score": round(avg_score, 2),
        "summary": f"Calculated based on {total} marketplace review(s) with an average score of {round(avg_score, 2)}/5.0.",
        "strengths": strengths,
        "improvement_areas": improvement_areas,
        "recurring_themes": ["Project delivery", "Client collaboration"],
        "advisory_recommendations": recommendations,
        "analysis_source": "SYSTEM_FALLBACK",
    }


def analyze_reviews_with_gemini(reviews_data, user_context=None):
    """
    Send review records to Gemini for advisory analysis.
    Returns structured JSON analysis or falls back gracefully on any error.
    """
    if not reviews_data:
        return generate_fallback_analysis(reviews_data, user_context)

    api_key = get_gemini_api_key()
    if not api_key:
        logger.info("GEMINI_API_KEY is not configured; using deterministic fallback analysis.")
        return generate_fallback_analysis(reviews_data, user_context)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        model_name = get_gemini_model()

        user_info = user_context or {}
        username = user_info.get("username", "Student/Freelancer")
        role = user_info.get("role", "STUDENT")

        prompt = (
            f"You are an advisory AI analysis engine for the NEXUS Student Freelancing Platform.\n"
            f"Your task is to analyze the following verified marketplace reviews for user '{username}' (Role: {role}).\n"
            f"Reviews data:\n{json.dumps(reviews_data, indent=2)}\n\n"
            f"Provide an objective, constructive, and advisory feedback summary.\n"
            f"IMPORTANT: You are purely ADVISORY. Do not make permanent decisions.\n"
            f"Output MUST be valid JSON conforming exactly to this structure:\n"
            f"{{\n"
            f'  "overall_sentiment": "POSITIVE" | "NEUTRAL" | "MIXED" | "NEGATIVE",\n'
            f'  "sentiment_score": float (1.0 to 5.0),\n'
            f'  "summary": "Concise 2-3 sentence overview of the performance feedback.",\n'
            f'  "strengths": ["string", "string"],\n'
            f'  "improvement_areas": ["string", "string"],\n'
            f'  "recurring_themes": ["string", "string"],\n'
            f'  "advisory_recommendations": ["Actionable tip 1", "Actionable tip 2"]\n'
            f"}}"
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        if response and response.text:
            cleaned_text = response.text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            parsed = json.loads(cleaned_text.strip())
            if isinstance(parsed, dict):
                valid_sentiments = {"POSITIVE", "NEUTRAL", "MIXED", "NEGATIVE", "NO_REVIEWS"}
                sentiment = str(parsed.get("overall_sentiment", "")).upper()
                if sentiment not in valid_sentiments:
                    sentiment = "NEUTRAL"

                try:
                    score = float(parsed.get("sentiment_score", 3.0))
                    score = max(1.0, min(5.0, round(score, 2)))
                except Exception:
                    score = 3.0

                summary = str(parsed.get("summary", "Review analysis summary."))
                strengths = [str(x) for x in parsed.get("strengths", [])] if isinstance(parsed.get("strengths"), list) else []
                improvement_areas = [str(x) for x in parsed.get("improvement_areas", [])] if isinstance(parsed.get("improvement_areas"), list) else []
                recurring_themes = [str(x) for x in parsed.get("recurring_themes", [])] if isinstance(parsed.get("recurring_themes"), list) else []
                advisory_recommendations = [str(x) for x in parsed.get("advisory_recommendations", [])] if isinstance(parsed.get("advisory_recommendations"), list) else []

                return {
                    "overall_sentiment": sentiment,
                    "sentiment_score": score,
                    "summary": summary,
                    "strengths": strengths,
                    "improvement_areas": improvement_areas,
                    "recurring_themes": recurring_themes,
                    "advisory_recommendations": advisory_recommendations,
                    "analysis_source": "GEMINI",
                }

    except Exception as e:
        logger.warning("Gemini review analysis call failed or encountered exception: %s", str(e))

    return generate_fallback_analysis(reviews_data, user_context)


# =====================================================================
# 2. CANDIDATE MATCHING (FOR JOB PROVIDERS)
# =====================================================================

def generate_candidate_matching_fallback(job_data, candidates_data):
    """
    Deterministic rule-based candidate matching engine when Gemini is unconfigured or offline.
    Guarantees reliable advisory matching based on real database attributes.
    """
    required_skills = [str(s).strip().lower() for s in job_data.get("required_skills", []) if s]

    ranked_candidates = []

    for c in candidates_data:
        student_skills = [str(s).strip().lower() for s in c.get("skills", []) if s]
        student_skills_orig = {str(s).strip().lower(): str(s).strip() for s in c.get("skills", []) if s}

        matching_skills = []
        for req in required_skills:
            for s in student_skills:
                if req in s or s in req:
                    matching_skills.append(student_skills_orig.get(s, req))
                    break
        matching_skills = list(dict.fromkeys(matching_skills))

        missing_skills = []
        for req in job_data.get("required_skills", []):
            if str(req).strip().lower() not in [m.lower() for m in matching_skills]:
                missing_skills.append(str(req).strip())

        score = 40
        if required_skills:
            skill_ratio = len(matching_skills) / len(required_skills)
            score += int(skill_ratio * 40)
        else:
            score += 20

        if c.get("portfolio_items"):
            score += min(10, len(c["portfolio_items"]) * 5)

        if c.get("has_applied"):
            score += 10

        score = max(0, min(100, score))

        if score >= 80:
            recommendation = "Strong match"
            reason = f"Excellent skill alignment ({len(matching_skills)}/{len(required_skills) if required_skills else 1} required skills) and relevant profile experience."
        elif score >= 60:
            recommendation = "Good match"
            reason = f"Solid background with key skills ({', '.join(matching_skills) if matching_skills else 'general background'}) matching project requirements."
        elif score >= 40:
            recommendation = "Potential match"
            reason = "Partial skill match; student may require brief onboarding on specific tools."
        else:
            recommendation = "Low match"
            reason = "Limited overlap with specific required technical skills."

        ranked_candidates.append({
            "student_id": c["student_id"],
            "student_name": c["student_name"],
            "username": c["username"],
            "match_score": score,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "reason": reason,
            "recommendation": recommendation,
            "has_applied": c.get("has_applied", False),
            "college": c.get("college", ""),
            "course": c.get("course", ""),
            "year_of_study": c.get("year_of_study", ""),
            "availability": c.get("availability", ""),
        })

    ranked_candidates.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "candidates": ranked_candidates,
        "analysis_source": "SYSTEM_FALLBACK",
    }


def match_candidates_with_gemini(job_data, candidates_data):
    """
    Send job requirements and candidate profiles to Gemini for AI candidate scoring and advisory match rationales.
    Falls back to deterministic matching on any failure or missing key.
    """
    if not candidates_data:
        return {"candidates": [], "analysis_source": "SYSTEM_FALLBACK"}

    api_key = get_gemini_api_key()
    if not api_key:
        logger.info("GEMINI_API_KEY is not configured; using deterministic candidate matching.")
        return generate_candidate_matching_fallback(job_data, candidates_data)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        model_name = get_gemini_model()

        prompt = (
            f"You are an advisory AI evaluation engine for the NEXUS Student Freelancing Platform.\n"
            f"Evaluate how well each student candidate matches the following Job Requirements.\n\n"
            f"JOB DETAILS:\n"
            f"- Title: {job_data.get('title')}\n"
            f"- Description: {job_data.get('description')}\n"
            f"- Required Skills: {json.dumps(job_data.get('required_skills', []))}\n"
            f"- Budget: ${job_data.get('budget')}\n\n"
            f"CANDIDATES DATA:\n{json.dumps(candidates_data, indent=2)}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Compare required job skills with candidate skills, portfolio items, bio, and application message.\n"
            f"2. Assign a match_score (integer between 0 and 100).\n"
            f"3. Identify matching_skills and missing_skills accurately from provided data.\n"
            f"4. Provide a 1-2 sentence constructive rationale in 'reason'.\n"
            f"5. Categorize 'recommendation' as one of: 'Strong match', 'Good match', 'Potential match', 'Low match'.\n"
            f"6. IMPORTANT: You are purely ADVISORY. Do not make permanent hiring decisions.\n\n"
            f"Output MUST be valid JSON conforming exactly to this structure:\n"
            f"{{\n"
            f'  "candidates": [\n'
            f"    {{\n"
            f'      "student_id": "string",\n'
            f'      "match_score": int,\n'
            f'      "matching_skills": ["skill1", "skill2"],\n'
            f'      "missing_skills": ["skill3"],\n'
            f'      "reason": "1-2 sentence explanation",\n'
            f'      "recommendation": "Strong match" | "Good match" | "Potential match" | "Low match"\n'
            f"    }}\n"
            f"  ]\n"
            f"}}"
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        if response and response.text:
            cleaned_text = response.text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            parsed = json.loads(cleaned_text.strip())
            ai_candidates = parsed.get("candidates", []) if isinstance(parsed, dict) else []

            cand_map = {c["student_id"]: c for c in candidates_data}
            merged = []
            seen_ids = set()
            valid_recommendations = {"Strong match", "Good match", "Potential match", "Low match"}

            if isinstance(ai_candidates, list):
                for ai_c in ai_candidates:
                    if not isinstance(ai_c, dict):
                        continue
                    sid = str(ai_c.get("student_id", "")).strip()
                    # CRITICAL: Reject hallucinated, unknown, or duplicate student_id
                    if not sid or sid not in cand_map or sid in seen_ids:
                        continue

                    seen_ids.add(sid)
                    orig = cand_map[sid]

                    try:
                        raw_score = int(ai_c.get("match_score", 50))
                        score = max(0, min(100, raw_score))
                    except Exception:
                        score = 50

                    rec = str(ai_c.get("recommendation", "Good match")).strip()
                    if rec not in valid_recommendations:
                        rec = "Good match"

                    matching_skills = [str(s) for s in ai_c.get("matching_skills", [])] if isinstance(ai_c.get("matching_skills"), list) else []
                    missing_skills = [str(s) for s in ai_c.get("missing_skills", [])] if isinstance(ai_c.get("missing_skills"), list) else []
                    reason = str(ai_c.get("reason", "Profile matches job requirements."))

                    merged.append({
                        "student_id": sid,
                        "student_name": orig.get("student_name", "Student"),
                        "username": orig.get("username", ""),
                        "match_score": score,
                        "matching_skills": matching_skills,
                        "missing_skills": missing_skills,
                        "reason": reason,
                        "recommendation": rec,
                        "has_applied": orig.get("has_applied", False),
                        "college": orig.get("college", ""),
                        "course": orig.get("course", ""),
                        "year_of_study": orig.get("year_of_study", ""),
                        "availability": orig.get("availability", ""),
                    })

            if merged:
                merged.sort(key=lambda x: x["match_score"], reverse=True)
                return {
                    "candidates": merged,
                    "analysis_source": "GEMINI",
                }

    except Exception as e:
        logger.warning("Gemini candidate matching call failed or encountered exception: %s", str(e))

    return generate_candidate_matching_fallback(job_data, candidates_data)


# =====================================================================
# 3. JOB RECOMMENDATIONS (FOR STUDENTS)
# =====================================================================

def generate_job_recommendations_fallback(student_data, jobs_data):
    """
    Deterministic rule-based job recommendation engine when Gemini is unconfigured or offline.
    Ranks open jobs according to student skills, bio keywords, and portfolio overlap.
    """
    student_skills = [str(s).strip().lower() for s in student_data.get("skills", []) if s]
    student_skills_orig = {str(s).strip().lower(): str(s).strip() for s in student_data.get("skills", []) if s}
    bio_text = (student_data.get("bio", "") + " " + student_data.get("course", "")).lower()

    ranked_jobs = []

    for job in jobs_data:
        required_skills = [str(s).strip().lower() for s in job.get("required_skills", []) if s]
        required_skills_orig = {str(s).strip().lower(): str(s).strip() for s in job.get("required_skills", []) if s}

        matching_skills = []
        for req in required_skills:
            for s in student_skills:
                if req in s or s in req:
                    matching_skills.append(required_skills_orig.get(req, req))
                    break
        matching_skills = list(dict.fromkeys(matching_skills))

        missing_skills = []
        for req in job.get("required_skills", []):
            if str(req).strip().lower() not in [m.lower() for m in matching_skills]:
                missing_skills.append(str(req).strip())

        # Base score calculation
        score = 35
        if required_skills:
            skill_ratio = len(matching_skills) / len(required_skills)
            score += int(skill_ratio * 45)
        else:
            score += 25

        # Background / bio overlap
        job_words = (job.get("title", "") + " " + job.get("description", "")).lower()
        if any(w in job_words for w in student_skills if len(w) > 3):
            score += 10
        if any(w in job_words for w in bio_text.split() if len(w) > 4):
            score += 5

        # Portfolio bonus
        if student_data.get("portfolio_items"):
            score += 5

        score = max(0, min(100, score))

        if score >= 80:
            recommendation = "Strong match"
            reason = f"Excellent match for your technical skills ({', '.join(matching_skills) if matching_skills else 'relevant skills'}) and profile background."
        elif score >= 60:
            recommendation = "Good match"
            reason = f"Good alignment with your skillset in {', '.join(matching_skills) if matching_skills else 'core tools'}."
        elif score >= 40:
            recommendation = "Potential match"
            reason = "Relevant opportunity that aligns with your broad development experience."
        else:
            recommendation = "Low match"
            reason = "Limited overlap with your primary listed skills."

        ranked_jobs.append({
            "job_id": job["id"],
            "title": job["title"],
            "description": job.get("description", ""),
            "match_score": score,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "reason": reason,
            "recommendation": recommendation,
            "budget": str(job.get("budget", "0")),
            "deadline": job.get("deadline"),
            "job_state": job.get("status", "POSTED"),
            "is_advisory": True,
        })

    ranked_jobs.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "recommendations": ranked_jobs,
        "analysis_source": "SYSTEM_FALLBACK",
    }


def recommend_jobs_with_gemini(student_data, jobs_data):
    """
    Send student profile and available jobs to Gemini for advisory job recommendation rankings.
    Falls back to deterministic matching on any failure or missing key.
    """
    if not jobs_data:
        return {"recommendations": [], "analysis_source": "SYSTEM_FALLBACK"}

    api_key = get_gemini_api_key()
    if not api_key:
        logger.info("GEMINI_API_KEY is not configured; using deterministic job recommendations.")
        return generate_job_recommendations_fallback(student_data, jobs_data)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        model_name = get_gemini_model()

        prompt = (
            f"You are an advisory AI career recommendation engine for the NEXUS Student Freelancing Platform.\n"
            f"Evaluate the following available freelance jobs for this student and provide ranked advisory job recommendations.\n\n"
            f"STUDENT PROFILE:\n"
            f"- Name: {student_data.get('student_name')}\n"
            f"- College: {student_data.get('college')}\n"
            f"- Course: {student_data.get('course')}\n"
            f"- Year of Study: {student_data.get('year_of_study')}\n"
            f"- Bio: {student_data.get('bio')}\n"
            f"- Availability: {student_data.get('availability')}\n"
            f"- Listed Skills: {json.dumps(student_data.get('skills', []))}\n"
            f"- Portfolio Summary: {json.dumps(student_data.get('portfolio_items', []))}\n\n"
            f"AVAILABLE JOBS:\n{json.dumps(jobs_data, indent=2)}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Compare student skills, course background, portfolio, and bio against each job's requirements and description.\n"
            f"2. Assign a match_score (integer between 0 and 100).\n"
            f"3. Identify matching_skills and missing_skills accurately from provided data.\n"
            f"4. Provide a 1-2 sentence constructive rationale in 'reason'.\n"
            f"5. Categorize 'recommendation' as one of: 'Strong match', 'Good match', 'Potential match', 'Low match'.\n"
            f"6. IMPORTANT: You are purely ADVISORY. Do not make permanent hiring decisions or auto-apply.\n\n"
            f"Output MUST be valid JSON conforming exactly to this structure:\n"
            f"{{\n"
            f'  "recommendations": [\n'
            f"    {{\n"
            f'      "job_id": "string",\n'
            f'      "match_score": int,\n'
            f'      "matching_skills": ["skill1", "skill2"],\n'
            f'      "missing_skills": ["skill3"],\n'
            f'      "reason": "1-2 sentence explanation",\n'
            f'      "recommendation": "Strong match" | "Good match" | "Potential match" | "Low match"\n'
            f"    }}\n"
            f"  ]\n"
            f"}}"
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        if response and response.text:
            cleaned_text = response.text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            parsed = json.loads(cleaned_text.strip())
            ai_recs = parsed.get("recommendations", []) if isinstance(parsed, dict) else []

            job_map = {j["id"]: j for j in jobs_data}
            merged = []
            seen_jobs = set()
            valid_recommendations = {"Strong match", "Good match", "Potential match", "Low match"}

            if isinstance(ai_recs, list):
                for r in ai_recs:
                    if not isinstance(r, dict):
                        continue
                    jid = str(r.get("job_id", "")).strip()
                    # CRITICAL: Reject hallucinated, unknown, or duplicate job_id
                    if not jid or jid not in job_map or jid in seen_jobs:
                        continue

                    seen_jobs.add(jid)
                    orig_job = job_map[jid]

                    try:
                        raw_score = int(r.get("match_score", 50))
                        score = max(0, min(100, raw_score))
                    except Exception:
                        score = 50

                    rec = str(r.get("recommendation", "Good match")).strip()
                    if rec not in valid_recommendations:
                        rec = "Good match"

                    matching_skills = [str(s) for s in r.get("matching_skills", [])] if isinstance(r.get("matching_skills"), list) else []
                    missing_skills = [str(s) for s in r.get("missing_skills", [])] if isinstance(r.get("missing_skills"), list) else []
                    reason = str(r.get("reason", "Matches your profile skills and experience."))

                    merged.append({
                        "job_id": jid,
                        "title": orig_job.get("title", "Freelance Job"),
                        "description": orig_job.get("description", ""),
                        "match_score": score,
                        "matching_skills": matching_skills,
                        "missing_skills": missing_skills,
                        "reason": reason,
                        "recommendation": rec,
                        "budget": str(orig_job.get("budget", "0")),
                        "deadline": orig_job.get("deadline"),
                        "job_state": orig_job.get("status", "POSTED"),
                        "is_advisory": True,
                    })

            if merged:
                merged.sort(key=lambda x: x["match_score"], reverse=True)
                return {
                    "recommendations": merged,
                    "analysis_source": "GEMINI",
                }

    except Exception as e:
        logger.warning("Gemini job recommendations call failed or encountered exception: %s", str(e))

    return generate_job_recommendations_fallback(student_data, jobs_data)


# =====================================================================
# 4. PROFILE IMPROVEMENT (FOR STUDENTS)
# =====================================================================

def generate_profile_improvement_fallback(student_data):
    """
    Deterministic rule-based profile improvement engine when Gemini is unconfigured or offline.
    Analyzes real student database attributes to identify missing information and provide actionable advice.
    """
    profile_improvements = []
    portfolio_improvements = []
    skill_presentation = []
    missing_information = []
    actionable_recommendations = []

    bio = (student_data.get("bio") or "").strip()
    college = (student_data.get("college") or "").strip()
    course = (student_data.get("course") or "").strip()
    year_of_study = (student_data.get("year_of_study") or "").strip()
    availability = (student_data.get("availability") or "").strip()
    skills = student_data.get("skills") or []
    portfolio_items = student_data.get("portfolio_items") or []

    # 1. Bio analysis
    if not bio:
        missing_information.append("Professional Bio")
        profile_improvements.append({
            "area": "Bio Summary",
            "suggestion": "Add a professional bio highlighting your academic background, core programming skills, and freelance availability.",
            "priority": "HIGH",
        })
    elif len(bio) < 40:
        profile_improvements.append({
            "area": "Bio Detail",
            "suggestion": "Expand your bio with more details about past project achievements and specific technical interests.",
            "priority": "MEDIUM",
        })
    else:
        profile_improvements.append({
            "area": "Bio Summary",
            "suggestion": "Ensure your bio clearly emphasizes your primary tech stack and preferred freelance project types.",
            "priority": "LOW",
        })

    # 2. Education & Availability check
    if not college:
        missing_information.append("College / University Name")
    if not course:
        missing_information.append("Course / Major")
    if not year_of_study:
        missing_information.append("Year of Study")
    if not availability:
        missing_information.append("Weekly Availability")
        profile_improvements.append({
            "area": "Availability Information",
            "suggestion": "Specify your weekly availability (e.g., '15-20 hours/week') so clients know your bandwith.",
            "priority": "HIGH",
        })

    # 3. Skills analysis
    if not skills:
        missing_information.append("Listed Technical Skills")
        skill_presentation.append({
            "suggestion": "Add key technical skills and tools (e.g., Python, React, SQL) to match client job requirements.",
            "priority": "HIGH",
        })
    elif len(skills) < 3:
        skill_presentation.append({
            "suggestion": "Add additional secondary skills or relevant tools to broaden your match scope for freelance jobs.",
            "priority": "MEDIUM",
        })
    else:
        skill_presentation.append({
            "suggestion": f"Your profile features {len(skills)} skills. Keep them updated with your latest framework proficiencies.",
            "priority": "LOW",
        })

    # 4. Portfolio analysis
    if not portfolio_items:
        missing_information.append("Portfolio Projects")
        portfolio_improvements.append({
            "suggestion": "Upload at least 1-2 portfolio items featuring project descriptions and code repository links.",
            "priority": "HIGH",
        })
    else:
        has_urls = any(p.get("project_url") for p in portfolio_items)
        if not has_urls:
            portfolio_improvements.append({
                "suggestion": "Add live demo URLs or GitHub repository links to your existing portfolio entries.",
                "priority": "MEDIUM",
            })
        else:
            portfolio_improvements.append({
                "suggestion": "Maintain clear, impact-focused project descriptions detailing technologies used and problems solved.",
                "priority": "LOW",
            })

    # 5. Actionable recommendations synthesis
    if missing_information:
        actionable_recommendations.append(
            f"Complete missing profile fields: {', '.join(missing_information[:3])}."
        )
    if not portfolio_items:
        actionable_recommendations.append("Create your first portfolio project entry to showcase verified capabilities.")
    actionable_recommendations.append("Review job recommendations regularly to align your skills with marketplace demand.")

    return {
        "profile_improvements": profile_improvements,
        "portfolio_improvements": portfolio_improvements,
        "skill_presentation": skill_presentation,
        "missing_information": missing_information,
        "actionable_recommendations": actionable_recommendations,
        "analysis_source": "SYSTEM_FALLBACK",
    }


def improve_profile_with_gemini(student_data):
    """
    Send student profile data to Gemini for AI profile improvement suggestions.
    Falls back gracefully to deterministic advice on any failure or unconfigured key.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        logger.info("GEMINI_API_KEY is not configured; using deterministic profile improvement suggestions.")
        return generate_profile_improvement_fallback(student_data)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        model_name = get_gemini_model()

        # Sanitize profile payload sent to Gemini (never send secrets/passwords/tokens)
        prompt_data = {
            "name": student_data.get("student_name"),
            "college": student_data.get("college"),
            "course": student_data.get("course"),
            "year_of_study": student_data.get("year_of_study"),
            "bio": student_data.get("bio"),
            "availability": student_data.get("availability"),
            "skills": student_data.get("skills", []),
            "portfolio_items": [
                {
                    "title": p.get("title"),
                    "description": p.get("description"),
                    "skills": p.get("skills"),
                    "project_url": p.get("project_url"),
                }
                for p in student_data.get("portfolio_items", [])
            ],
        }

        prompt = (
            f"You are an advisory AI career coach for the NEXUS Student Freelancing Platform.\n"
            f"Analyze the following real student profile and provide actionable, constructive suggestions to improve their profile visibility and freelance readiness.\n\n"
            f"STUDENT PROFILE DATA:\n{json.dumps(prompt_data, indent=2)}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Evaluate bio clarity, completeness of college/course/availability information, skill presentation, and portfolio quality.\n"
            f"2. Identify missing profile information.\n"
            f"3. Assign priority ('HIGH', 'MEDIUM', 'LOW') to each suggestion.\n"
            f"4. Provide 3-5 clear actionable steps in 'actionable_recommendations'.\n"
            f"5. IMPORTANT: You are purely ADVISORY. Do NOT modify the profile.\n\n"
            f"Output MUST be valid JSON conforming exactly to this structure:\n"
            f"{{\n"
            f'  "profile_improvements": [\n'
            f'    {{"area": "string", "suggestion": "string", "priority": "HIGH" | "MEDIUM" | "LOW"}}\n'
            f'  ],\n'
            f'  "portfolio_improvements": [\n'
            f'    {{"suggestion": "string", "priority": "HIGH" | "MEDIUM" | "LOW"}}\n'
            f'  ],\n'
            f'  "skill_presentation": [\n'
            f'    {{"suggestion": "string", "priority": "HIGH" | "MEDIUM" | "LOW"}}\n'
            f'  ],\n'
            f'  "missing_information": ["field1", "field2"],\n'
            f'  "actionable_recommendations": ["step1", "step2"]\n'
            f"}}"
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        if response and response.text:
            cleaned_text = response.text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            parsed = json.loads(cleaned_text.strip())

            # Validate server-side standard structure and priority enums
            valid_priorities = {"HIGH", "MEDIUM", "LOW"}

            def sanitize_suggestions(items):
                sanitized = []
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            p = str(item.get("priority", "MEDIUM")).upper()
                            if p not in valid_priorities:
                                p = "MEDIUM"
                            sanitized.append({
                                **item,
                                "priority": p,
                            })
                return sanitized

            return {
                "profile_improvements": sanitize_suggestions(parsed.get("profile_improvements")),
                "portfolio_improvements": sanitize_suggestions(parsed.get("portfolio_improvements")),
                "skill_presentation": sanitize_suggestions(parsed.get("skill_presentation")),
                "missing_information": [str(x) for x in parsed.get("missing_information", [])] if isinstance(parsed.get("missing_information"), list) else [],
                "actionable_recommendations": [str(x) for x in parsed.get("actionable_recommendations", [])] if isinstance(parsed.get("actionable_recommendations"), list) else [],
                "analysis_source": "GEMINI",
            }

    except Exception as e:
        logger.warning("Gemini profile improvement call failed or encountered exception: %s", str(e))

    return generate_profile_improvement_fallback(student_data)


# =====================================================================
# 5. SKILL SUGGESTIONS (FOR STUDENTS)
# =====================================================================

def generate_skill_suggestions_fallback(student_data, marketplace_jobs=None):
    """
    Deterministic rule-based skill recommendation engine when Gemini is unconfigured or offline.
    Identifies marketplace skill demands and complementary tech stacks that the student does not currently possess.
    """
    existing_skills_lower = {
        str(s).strip().lower() for s in (student_data.get("skills") or []) if s
    }

    raw_candidates = []

    # 1. Inspect marketplace jobs for required skills not yet owned by student
    if marketplace_jobs:
        job_skill_counts = {}
        for job in marketplace_jobs:
            req_skills = job.get("required_skills") or []
            for req in req_skills:
                req_clean = str(req).strip()
                if req_clean and req_clean.lower() not in existing_skills_lower:
                    job_skill_counts[req_clean] = job_skill_counts.get(req_clean, 0) + 1

        for sk, count in sorted(job_skill_counts.items(), key=lambda x: x[1], reverse=True):
            relevance = "HIGH" if count >= 2 else "MEDIUM"
            raw_candidates.append({
                "skill": sk,
                "reason": f"High demand skill listed in {count} active marketplace job(s).",
                "relevance": relevance,
                "is_advisory": True,
            })

    # 2. Add domain-specific complementary fallbacks if candidates are sparse
    complementary_map = {
        "python": [("Docker", "Containerization simplifies python backend deployment."), ("FastAPI", "Modern async web framework in high demand."), ("PostgreSQL", "Essential relational database for python applications.")],
        "django": [("REST APIs", "Essential for building decoupled frontend/backend services."), ("Celery", "Asynchronous task queue commonly paired with Django."), ("Redis", "In-memory caching engine used for scalable backends.")],
        "react": [("TypeScript", "Adds static typing for scalable React applications."), ("Next.js", "Popular full-stack React framework for web production."), ("Tailwind CSS", "Utility-first CSS framework popular in modern frontend development.")],
        "figma": [("UI/UX Research", "Strengthens design rationale and user testing methodology."), ("Prototyping", "Helps communicate interactive design micro-interactions."), ("Design Systems", "High-value skill for scalable component design.")],
        "javascript": [("Node.js", "Enables server-side JavaScript development."), ("TypeScript", "Improves code quality and type safety for JS projects.")],
    }

    for owned_skill in list(existing_skills_lower):
        for key, comp_list in complementary_map.items():
            if key in owned_skill:
                for comp_skill, reason in comp_list:
                    if comp_skill.lower() not in existing_skills_lower:
                        if not any(c["skill"].lower() == comp_skill.lower() for c in raw_candidates):
                            raw_candidates.append({
                                "skill": comp_skill,
                                "reason": reason,
                                "relevance": "MEDIUM",
                                "is_advisory": True,
                            })

    # Generic fallback skills if profile is sparse
    generic_fallbacks = [
        ("Git & GitHub", "Fundamental version control tool required across all software projects.", "HIGH"),
        ("RESTful API Design", "Core web architecture skill valued across web development jobs.", "MEDIUM"),
        ("SQL & Database Basics", "Essential skill for data persistence and backend development.", "MEDIUM"),
    ]

    for sk, reason, rel in generic_fallbacks:
        if sk.lower() not in existing_skills_lower:
            if not any(c["skill"].lower() == sk.lower() for c in raw_candidates):
                raw_candidates.append({
                    "skill": sk,
                    "reason": reason,
                    "relevance": rel,
                    "is_advisory": True,
                })

    # Strict server-side filter against existing skills
    filtered_suggestions = []
    seen = set()
    for cand in raw_candidates:
        sk_name = str(cand.get("skill", "")).strip()
        sk_lower = sk_name.lower()
        if sk_name and sk_lower not in existing_skills_lower and sk_lower not in seen:
            seen.add(sk_lower)
            filtered_suggestions.append({
                "skill": sk_name,
                "reason": str(cand.get("reason", "Useful skill for your background.")),
                "relevance": str(cand.get("relevance", "MEDIUM")).upper(),
                "is_advisory": True,
            })

    return {
        "suggestions": filtered_suggestions[:10],
        "analysis_source": "SYSTEM_FALLBACK",
    }


def suggest_skills_with_gemini(student_data, marketplace_jobs=None):
    """
    Send student profile, current skills, and active job market requirements to Gemini
    for AI skill recommendations.
    Enforces server-side validation and filtering to ensure existing skills are NEVER recommended.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        logger.info("GEMINI_API_KEY is not configured; using deterministic skill suggestions.")
        return generate_skill_suggestions_fallback(student_data, marketplace_jobs)

    existing_skills_lower = {
        str(s).strip().lower() for s in (student_data.get("skills") or []) if s
    }

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        model_name = get_gemini_model()

        prompt_data = {
            "name": student_data.get("student_name"),
            "course": student_data.get("course"),
            "bio": student_data.get("bio"),
            "current_skills": student_data.get("skills", []),
            "portfolio_items": [
                {
                    "title": p.get("title"),
                    "skills": p.get("skills"),
                }
                for p in student_data.get("portfolio_items", [])
            ],
            "sample_marketplace_jobs": [
                {
                    "title": j.get("title"),
                    "required_skills": j.get("required_skills", []),
                }
                for j in (marketplace_jobs or [])[:10]
            ],
        }

        prompt = (
            f"You are an advisory AI skill advisor for the NEXUS Student Freelancing Platform.\n"
            f"Analyze the student's background and recommend additional technical/domain skills to improve their freelance job suitability.\n\n"
            f"STUDENT CONTEXT DATA:\n{json.dumps(prompt_data, indent=2)}\n\n"
            f"CRITICAL BUSINESS RULE:\n"
            f"Do NOT recommend any skill that the student ALREADY possesses in 'current_skills':\n"
            f"{json.dumps(student_data.get('skills', []))}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Identify 3-6 NEW complementary skills that would expand the student's freelance opportunities.\n"
            f"2. Provide a 1-sentence explanation of why each skill is beneficial in 'reason'.\n"
            f"3. Assign relevance ('HIGH', 'MEDIUM', 'LOW').\n"
            f"4. IMPORTANT: You are purely ADVISORY. Do NOT create or modify skill records.\n\n"
            f"Output MUST be valid JSON conforming exactly to this structure:\n"
            f"{{\n"
            f'  "suggestions": [\n'
            f'    {{\n'
            f'      "skill": "string",\n'
            f'      "reason": "1-sentence explanation",\n'
            f'      "relevance": "HIGH" | "MEDIUM" | "LOW"\n'
            f'    }}\n'
            f'  ]\n'
            f"}}"
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        if response and response.text:
            cleaned_text = response.text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            parsed = json.loads(cleaned_text.strip())
            suggestions_raw = parsed.get("suggestions", [])

            valid_relevances = {"HIGH", "MEDIUM", "LOW"}
            sanitized_suggestions = []
            seen = set()

            if isinstance(suggestions_raw, list):
                for item in suggestions_raw:
                    if isinstance(item, dict):
                        sk = str(item.get("skill", "")).strip()
                        sk_lower = sk.lower()
                        # Strict server-side filter: reject empty, duplicate, or existing skills
                        if sk and sk_lower not in existing_skills_lower and sk_lower not in seen and len(sk) <= 100:
                            seen.add(sk_lower)
                            rel = str(item.get("relevance", "MEDIUM")).upper()
                            if rel not in valid_relevances:
                                rel = "MEDIUM"
                            sanitized_suggestions.append({
                                "skill": sk,
                                "reason": str(item.get("reason", "Helpful skill for your development focus.")),
                                "relevance": rel,
                                "is_advisory": True,
                            })

            return {
                "suggestions": sanitized_suggestions,
                "analysis_source": "GEMINI",
            }

    except Exception as e:
        logger.warning("Gemini skill suggestions call failed or encountered exception: %s", str(e))

    return generate_skill_suggestions_fallback(student_data, marketplace_jobs)


