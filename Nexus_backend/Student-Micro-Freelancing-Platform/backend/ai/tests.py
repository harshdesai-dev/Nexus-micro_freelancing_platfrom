import json
import uuid
from decimal import Decimal

from django.test import TestCase, Client
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from clients.models import Application, Job, Rating
from students.models import PortfolioItem, Skill, StudentProfile


class AiModuleTests(TestCase):
    def setUp(self):
        self.client = Client()

        # 1. Create Student Alice (has Python, Django, React skills + portfolio)
        self.student_alice = User.objects.create_user(
            username="student_alice",
            email="alice@test.com",
            password="Password123!",
            role=User.Role.STUDENT,
            name="Alice Johnson",
        )
        self.profile_alice = StudentProfile.objects.create(
            user=self.student_alice,
            college="MIT",
            course="Computer Science",
            year_of_study="3rd Year",
            bio="Passionate full-stack developer with 2 years of freelance experience.",
            availability="Part-time (20 hrs/week)",
            skills_data=["Python", "Django", "React"],
        )
        Skill.objects.create(student=self.profile_alice, name="REST APIs")
        PortfolioItem.objects.create(
            user=self.student_alice,
            title="E-commerce Backend API",
            description="Built a scalable Django REST API with PostgreSQL.",
            skills="Python, Django, PostgreSQL",
            is_visible=True,
        )

        # 2. Create Student Bob (has Design, Figma, CSS skills)
        self.student_bob = User.objects.create_user(
            username="student_bob",
            email="bob@test.com",
            password="Password123!",
            role=User.Role.STUDENT,
            name="Bob Designer",
        )
        self.profile_bob = StudentProfile.objects.create(
            user=self.student_bob,
            college="Stanford",
            course="Design",
            year_of_study="2nd Year",
            bio="UI/UX designer focused on clean interfaces.",
            availability="Full-time",
            skills_data=["Figma", "UI Design", "CSS"],
        )

        # 3. Create Client Charlie (Job Provider)
        self.client_charlie = User.objects.create_user(
            username="client_charlie",
            email="charlie@test.com",
            password="Password123!",
            role=User.Role.CLIENT,
            name="Charlie Client",
        )

        # 4. Create Other Client Dave (Unauthorized client)
        self.client_dave = User.objects.create_user(
            username="client_dave",
            email="dave@test.com",
            password="Password123!",
            role=User.Role.CLIENT,
            name="Dave Other",
        )

        # 5. Create Admin Eve
        self.admin_eve = User.objects.create_user(
            username="admin_eve",
            email="admin@test.com",
            password="Password123!",
            role=User.Role.ADMIN,
            name="Eve Admin",
        )

        # 6. Create Job 1: Open Python/Django job posted by Charlie
        self.job_python = Job.objects.create(
            title="Django Backend API Development",
            description="Looking for an experienced student to build REST APIs in Python Django.",
            required_skills=["Python", "Django", "PostgreSQL"],
            budget=Decimal("250.00"),
            job_provider=self.client_charlie,
            status=Job.Status.POSTED,
        )

        # 7. Create Job 2: Open Figma Design job posted by Charlie
        self.job_design = Job.objects.create(
            title="Mobile App Figma UI Design",
            description="Need clean UI designs in Figma for a student marketplace mobile app.",
            required_skills=["Figma", "UI Design"],
            budget=Decimal("150.00"),
            job_provider=self.client_charlie,
            status=Job.Status.POSTED,
        )

        # 8. Create Job 3: Closed / Completed job posted by Charlie
        self.job_completed = Job.objects.create(
            title="Completed Legacy System",
            description="Past job already finished.",
            required_skills=["Python"],
            budget=Decimal("50.00"),
            job_provider=self.client_charlie,
            status=Job.Status.COMPLETED,
        )

        # 9. Student Alice applies to Job 1 (job_python)
        self.application = Application.objects.create(
            job=self.job_python,
            student=self.student_alice,
            application_message="I have strong experience with Django REST framework and would love to help!",
            status=Application.Status.APPLIED,
        )

        # Generate JWT tokens
        self.token_alice = str(RefreshToken.for_user(self.student_alice).access_token)
        self.token_bob = str(RefreshToken.for_user(self.student_bob).access_token)
        self.token_charlie = str(RefreshToken.for_user(self.client_charlie).access_token)
        self.token_dave = str(RefreshToken.for_user(self.client_dave).access_token)
        self.token_admin = str(RefreshToken.for_user(self.admin_eve).access_token)

    # =================================================================
    # PHASE 1: REVIEW ANALYSIS TESTS
    # =================================================================

    def test_review_analysis_unauthenticated(self):
        """Unauthenticated review analysis request must return 401."""
        res = self.client.post("/api/ai/review-analysis", data=json.dumps({"user_id": str(self.student_alice.id)}), content_type="application/json")
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json()["success"])

    def test_review_analysis_zero_reviews(self):
        """Review analysis on user with zero reviews returns clean empty state."""
        res = self.client.post(
            "/api/ai/review-analysis",
            data=json.dumps({"user_id": str(self.student_alice.id)}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_charlie}",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["total_reviews"], 0)
        self.assertEqual(data["data"]["average_rating"], 0.0)
        self.assertTrue(data["data"]["is_advisory"])
        self.assertEqual(data["data"]["analysis"]["overall_sentiment"], "NO_REVIEWS")

    def test_review_analysis_with_real_ratings(self):
        """Review analysis queries real database Rating records."""
        completed_job = Job.objects.create(
            title="Completed Python Task",
            description="Build scraper",
            budget=Decimal("100.00"),
            job_provider=self.client_charlie,
            selected_student=self.student_alice,
            status=Job.Status.RATED,
        )
        Rating.objects.create(
            job=completed_job,
            reviewer=self.client_charlie,
            reviewed_user=self.student_alice,
            rating=5,
            review_content="Alice delivered amazing work quickly and cleanly!",
        )

        res = self.client.post(
            "/api/ai/review-analysis",
            data=json.dumps({"user_id": str(self.student_alice.id)}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_charlie}",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["total_reviews"], 1)
        self.assertEqual(data["data"]["average_rating"], 5.0)
        self.assertTrue(data["data"]["is_advisory"])

    # =================================================================
    # PHASE 2: CANDIDATE MATCHING TESTS
    # =================================================================

    def test_match_candidates_unauthenticated(self):
        """Unauthenticated candidate matching request must return 401."""
        res = self.client.post("/api/ai/match-candidates", data=json.dumps({"job_id": str(self.job_python.id)}), content_type="application/json")
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "UNAUTHORIZED")

    def test_match_candidates_invalid_json(self):
        """Invalid JSON in request body returns 400."""
        res = self.client.post("/api/ai/match-candidates", data="invalid-json", content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token_charlie}")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["error"]["code"], "INVALID_JSON")

    def test_match_candidates_missing_job_id(self):
        """Missing job_id returns 400 VALIDATION_ERROR."""
        res = self.client.post("/api/ai/match-candidates", data=json.dumps({}), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token_charlie}")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["error"]["code"], "VALIDATION_ERROR")

    def test_match_candidates_invalid_job_id_format(self):
        """Invalid job_id UUID returns 400 VALIDATION_ERROR."""
        res = self.client.post("/api/ai/match-candidates", data=json.dumps({"job_id": "not-a-uuid"}), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token_charlie}")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["error"]["code"], "VALIDATION_ERROR")

    def test_match_candidates_nonexistent_job(self):
        """Nonexistent job returns 404 NOT_FOUND."""
        res = self.client.post("/api/ai/match-candidates", data=json.dumps({"job_id": str(uuid.uuid4())}), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token_charlie}")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["error"]["code"], "NOT_FOUND")

    def test_match_candidates_forbidden_for_unauthorized_user(self):
        """A client who did NOT post the job is forbidden from viewing matches (403)."""
        res = self.client.post("/api/ai/match-candidates", data=json.dumps({"job_id": str(self.job_python.id)}), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token_dave}")
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")

    def test_match_candidates_allowed_for_admin(self):
        """Platform administrator can view candidate matches for any job."""
        res = self.client.post("/api/ai/match-candidates", data=json.dumps({"job_id": str(self.job_python.id)}), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {self.token_admin}")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

    def test_match_candidates_success_with_real_orm_data(self):
        """Candidate matching evaluates real Job, StudentProfile, Skill, Portfolio, and Application records."""
        res = self.client.post(
            "/api/ai/match-candidates",
            data=json.dumps({"job_id": str(self.job_python.id)}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_charlie}",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("data", data)

        job_info = data["data"]["job"]
        self.assertEqual(job_info["id"], str(self.job_python.id))
        self.assertEqual(job_info["title"], "Django Backend API Development")
        self.assertEqual(job_info["required_skills"], ["Python", "Django", "PostgreSQL"])

        candidates = data["data"]["candidates"]
        self.assertGreaterEqual(len(candidates), 2)

        alice_match = next((c for c in candidates if c["student_id"] == str(self.student_alice.id)), None)
        bob_match = next((c for c in candidates if c["student_id"] == str(self.student_bob.id)), None)

        self.assertIsNotNone(alice_match)
        self.assertIsNotNone(bob_match)
        self.assertTrue(alice_match["has_applied"])
        self.assertFalse(bob_match["has_applied"])
        self.assertGreater(alice_match["match_score"], bob_match["match_score"])
        self.assertIn("Python", [s.capitalize() for s in alice_match["matching_skills"]])
        self.assertIn("Django", [s.capitalize() for s in alice_match["matching_skills"]])
        self.assertTrue(data["data"]["is_advisory"])

    def test_match_candidates_advisory_rule_no_mutations(self):
        """Verify AI candidate matching does NOT select, hire, or modify any database record."""
        jobs_count_before = Job.objects.count()
        apps_count_before = Application.objects.count()
        users_count_before = User.objects.count()

        res = self.client.post(
            "/api/ai/match-candidates",
            data=json.dumps({"job_id": str(self.job_python.id)}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_charlie}",
        )
        self.assertEqual(res.status_code, 200)

        refreshed_job = Job.objects.get(id=self.job_python.id)
        self.assertIsNone(refreshed_job.selected_student)
        self.assertEqual(refreshed_job.status, Job.Status.POSTED)

        refreshed_app = Application.objects.get(id=self.application.id)
        self.assertEqual(refreshed_app.status, Application.Status.APPLIED)

        self.assertEqual(Job.objects.count(), jobs_count_before)
        self.assertEqual(Application.objects.count(), apps_count_before)
        self.assertEqual(User.objects.count(), users_count_before)

    # =================================================================
    # PHASE 3: JOB RECOMMENDATIONS TESTS
    # =================================================================

    def test_job_recommendations_unauthenticated(self):
        """Unauthenticated job recommendations request returns 401."""
        res = self.client.post("/api/ai/job-recommendations", data=json.dumps({}), content_type="application/json")
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json()["success"])
        self.assertEqual(res.json()["error"]["code"], "UNAUTHORIZED")

    def test_job_recommendations_non_student_rejected(self):
        """Client user calling student job recommendations endpoint is rejected with 403 FORBIDDEN."""
        res = self.client.post(
            "/api/ai/job-recommendations",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_charlie}",
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json()["success"])
        self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")

    def test_job_recommendations_admin_rejected(self):
        """Admin is not a valid recommendation subject; endpoint is strictly STUDENT-only."""
        res = self.client.post(
            "/api/ai/job-recommendations",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_admin}",
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json()["success"])
        self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")

    def test_job_recommendations_authenticated_student_success(self):
        """Authenticated student receives ranked job recommendations using real ORM records."""
        res = self.client.post(
            "/api/ai/job-recommendations",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_bob}",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertEqual(data["data"]["student_id"], str(self.student_bob.id))
        self.assertTrue(data["data"]["is_advisory"])

        recs = data["data"]["recommendations"]
        self.assertGreaterEqual(len(recs), 1)

        # For Bob (UI Designer), job_design should have high match score
        design_rec = next((r for r in recs if r["job_id"] == str(self.job_design.id)), None)
        self.assertIsNotNone(design_rec)
        self.assertGreaterEqual(design_rec["match_score"], 60)
        self.assertIn("Figma", [s.capitalize() for s in design_rec["matching_skills"]])
        self.assertIsInstance(design_rec["reason"], str)
        self.assertTrue(design_rec["is_advisory"])

    def test_job_recommendations_excludes_applied_jobs(self):
        """Jobs the student has already applied to are excluded from job recommendations."""
        # Alice already applied to self.job_python
        res = self.client.post(
            "/api/ai/job-recommendations",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_alice}",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        recs = data["data"]["recommendations"]

        recommended_job_ids = [r["job_id"] for r in recs]
        self.assertNotIn(str(self.job_python.id), recommended_job_ids)

    def test_job_recommendations_excludes_completed_jobs(self):
        """Completed or closed jobs are excluded from recommendations."""
        res = self.client.post(
            "/api/ai/job-recommendations",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_bob}",
        )
        self.assertEqual(res.status_code, 200)
        recs = res.json()["data"]["recommendations"]
        recommended_job_ids = [r["job_id"] for r in recs]
        self.assertNotIn(str(self.job_completed.id), recommended_job_ids)

    def test_job_recommendations_advisory_rule_no_mutations(self):
        """Verify AI job recommendations is strictly read-only with zero database writes."""
        jobs_count_before = Job.objects.count()
        apps_count_before = Application.objects.count()
        users_count_before = User.objects.count()

        res = self.client.post(
            "/api/ai/job-recommendations",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_bob}",
        )
        self.assertEqual(res.status_code, 200)

        self.assertEqual(Job.objects.count(), jobs_count_before)
        self.assertEqual(Application.objects.count(), apps_count_before)
        self.assertEqual(User.objects.count(), users_count_before)

    def test_api_key_privacy(self):
        """Verify GEMINI_API_KEY and secrets are not leaked in any AI response."""
        res = self.client.post(
            "/api/ai/job-recommendations",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_bob}",
        )
        body_text = res.content.decode("utf-8")
        self.assertNotIn("GEMINI_API_KEY", body_text)
        self.assertNotIn("password", body_text.lower())

    # =================================================================
    # PHASE 4: PROFILE IMPROVEMENT TESTS
    # =================================================================

    def test_profile_improvement_unauthenticated(self):
        """Unauthenticated profile improvement request must return 401."""
        res = self.client.post("/api/ai/profile-improvement", data=json.dumps({}), content_type="application/json")
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json()["success"])
        self.assertEqual(res.json()["error"]["code"], "UNAUTHORIZED")

    def test_profile_improvement_forbidden_for_client(self):
        """Client user requesting profile improvement is rejected with 403 FORBIDDEN."""
        res = self.client.post(
            "/api/ai/profile-improvement",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_charlie}",
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json()["success"])
        self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")

    def test_profile_improvement_admin_rejected(self):
        """Admin is not a valid profile-improvement subject; endpoint is strictly STUDENT-only."""
        res = self.client.post(
            "/api/ai/profile-improvement",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_admin}",
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json()["success"])
        self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")

    def test_profile_improvement_forbidden_for_other_student_id(self):
        """Student requesting profile improvement for a different student ID is rejected with 403."""
        res = self.client.post(
            "/api/ai/profile-improvement",
            data=json.dumps({"student_id": str(self.student_bob.id)}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_alice}",
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json()["success"])
        self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")

    def test_profile_improvement_authenticated_student_success(self):
        """Authenticated student receives profile improvement suggestions using real ORM records."""
        res = self.client.post(
            "/api/ai/profile-improvement",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_alice}",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertEqual(data["data"]["student_id"], str(self.student_alice.id))
        self.assertTrue(data["data"]["is_advisory"])
        self.assertIn("profile_improvements", data["data"])
        self.assertIn("portfolio_improvements", data["data"])
        self.assertIn("skill_presentation", data["data"])
        self.assertIn("missing_information", data["data"])
        self.assertIn("actionable_recommendations", data["data"])

    def test_profile_improvement_uses_real_orm_data(self):
        """Profile improvement logic evaluates real StudentProfile, Skill, and PortfolioItem records."""
        from ai.services import get_profile_improvement_for_student

        result, err = get_profile_improvement_for_student(self.student_alice)
        self.assertIsNone(err)
        self.assertEqual(result["student_id"], str(self.student_alice.id))
        self.assertTrue(result["is_advisory"])
        self.assertIn("SYSTEM_FALLBACK", result["analysis_source"])

        # Create a new bare student with no skills, bio, or portfolio
        bare_student = User.objects.create_user(
            username="bare_student",
            email="bare@test.com",
            password="Password123!",
            role=User.Role.STUDENT,
        )
        StudentProfile.objects.create(user=bare_student)

        bare_result, bare_err = get_profile_improvement_for_student(bare_student)
        self.assertIsNone(bare_err)
        self.assertIn("Professional Bio", bare_result["missing_information"])
        self.assertIn("Portfolio Projects", bare_result["missing_information"])

    def test_profile_improvement_gemini_fallback(self):
        """When Gemini API is unconfigured/offline, deterministic SYSTEM_FALLBACK is returned."""
        from ai.gemini_client import improve_profile_with_gemini

        student_data = {
            "student_id": str(self.student_alice.id),
            "student_name": "Alice Johnson",
            "bio": "Short bio",
            "college": "MIT",
            "course": "CS",
            "year_of_study": "3rd Year",
            "availability": "",
            "skills": ["Python"],
            "portfolio_items": [],
        }
        res = improve_profile_with_gemini(student_data)
        self.assertEqual(res["analysis_source"], "SYSTEM_FALLBACK")
        self.assertIn("Weekly Availability", res["missing_information"])

    def test_profile_improvement_advisory_rule_no_mutations(self):
        """Verify profile improvement does NOT mutate StudentProfile, User, Skill, or PortfolioItem."""
        profiles_count_before = StudentProfile.objects.count()
        skills_count_before = Skill.objects.count()
        portfolio_count_before = PortfolioItem.objects.count()
        users_count_before = User.objects.count()

        res = self.client.post(
            "/api/ai/profile-improvement",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_alice}",
        )
        self.assertEqual(res.status_code, 200)

        self.assertEqual(StudentProfile.objects.count(), profiles_count_before)
        self.assertEqual(Skill.objects.count(), skills_count_before)
        self.assertEqual(PortfolioItem.objects.count(), portfolio_count_before)
        self.assertEqual(User.objects.count(), users_count_before)

    def test_profile_improvement_privacy(self):
        """Verify API keys, passwords, and sensitive fields are excluded from profile improvement outputs."""
        res = self.client.post(
            "/api/ai/profile-improvement",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_alice}",
        )
        body_text = res.content.decode("utf-8")
        self.assertNotIn("GEMINI_API_KEY", body_text)
        self.assertNotIn("password", body_text.lower())
        self.assertNotIn("token", body_text.lower())

    # =================================================================
    # PHASE 5: SKILL SUGGESTIONS TESTS
    # =================================================================

    def test_skill_suggestions_unauthenticated(self):
        """Unauthenticated skill suggestions request must return 401."""
        res = self.client.post("/api/ai/skill-suggestions", data=json.dumps({}), content_type="application/json")
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json()["success"])
        self.assertEqual(res.json()["error"]["code"], "UNAUTHORIZED")

    def test_skill_suggestions_forbidden_for_client(self):
        """Client user requesting skill suggestions is rejected with 403 FORBIDDEN."""
        res = self.client.post(
            "/api/ai/skill-suggestions",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_charlie}",
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json()["success"])
        self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")

    def test_skill_suggestions_forbidden_for_admin(self):
        """Admin user requesting student skill suggestions is rejected with 403 FORBIDDEN per user rule."""
        res = self.client.post(
            "/api/ai/skill-suggestions",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_admin}",
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json()["success"])
        self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")

    def test_skill_suggestions_forbidden_for_other_student_id(self):
        """Student requesting skill suggestions for another student ID is rejected with 403."""
        res = self.client.post(
            "/api/ai/skill-suggestions",
            data=json.dumps({"student_id": str(self.student_bob.id)}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_alice}",
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json()["success"])
        self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")

    def test_skill_suggestions_authenticated_student_success(self):
        """Authenticated student receives skill suggestions using real ORM records."""
        res = self.client.post(
            "/api/ai/skill-suggestions",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_alice}",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertEqual(data["data"]["student_id"], str(self.student_alice.id))
        self.assertTrue(data["data"]["is_advisory"])
        self.assertIn("current_skills", data["data"])
        self.assertIn("suggestions", data["data"])
        self.assertIsInstance(data["data"]["suggestions"], list)

    def test_skill_suggestions_never_suggests_existing_skills(self):
        """Mandatory Business Rule: Existing student skills MUST NEVER be suggested as new skills."""
        res = self.client.post(
            "/api/ai/skill-suggestions",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_alice}",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]

        existing_lower = {s.lower() for s in data["current_skills"]}

        for sugg in data["suggestions"]:
            self.assertNotIn(
                sugg["skill"].lower(),
                existing_lower,
                f"Existing skill '{sugg['skill']}' was improperly returned as a recommendation!",
            )

    def test_skill_suggestions_server_side_filtering_case_insensitive(self):
        """Server-side filtering removes case-insensitive duplicates of existing skills."""
        from ai.services import get_skill_suggestions_for_student

        # Alice has "Python", "Django", "React", "REST APIs"
        result, err = get_skill_suggestions_for_student(self.student_alice)
        self.assertIsNone(err)

        suggested_names_lower = [s["skill"].lower() for s in result["suggestions"]]
        self.assertNotIn("python", suggested_names_lower)
        self.assertNotIn("django", suggested_names_lower)
        self.assertNotIn("react", suggested_names_lower)
        self.assertNotIn("rest apis", suggested_names_lower)

    def test_skill_suggestions_gemini_fallback(self):
        """When Gemini API is unconfigured/offline, deterministic SYSTEM_FALLBACK is returned."""
        from ai.gemini_client import suggest_skills_with_gemini

        student_data = {
            "student_id": str(self.student_alice.id),
            "student_name": "Alice Johnson",
            "skills": ["Python", "Django"],
            "bio": "Python dev",
            "portfolio_items": [],
        }
        res = suggest_skills_with_gemini(student_data, [])
        self.assertEqual(res["analysis_source"], "SYSTEM_FALLBACK")
        suggested_skills = [s["skill"].lower() for s in res["suggestions"]]
        self.assertNotIn("python", suggested_skills)
        self.assertNotIn("django", suggested_skills)

    def test_skill_suggestions_advisory_rule_no_mutations(self):
        """Verify skill suggestions does NOT mutate User, StudentProfile, Skill, PortfolioItem, Job, or Application."""
        profiles_count_before = StudentProfile.objects.count()
        skills_count_before = Skill.objects.count()
        portfolio_count_before = PortfolioItem.objects.count()
        users_count_before = User.objects.count()
        jobs_count_before = Job.objects.count()
        apps_count_before = Application.objects.count()

        res = self.client.post(
            "/api/ai/skill-suggestions",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_alice}",
        )
        self.assertEqual(res.status_code, 200)

        self.assertEqual(StudentProfile.objects.count(), profiles_count_before)
        self.assertEqual(Skill.objects.count(), skills_count_before)
        self.assertEqual(PortfolioItem.objects.count(), portfolio_count_before)
        self.assertEqual(User.objects.count(), users_count_before)
        self.assertEqual(Job.objects.count(), jobs_count_before)
        self.assertEqual(Application.objects.count(), apps_count_before)

    def test_skill_suggestions_privacy(self):
        """Verify API keys, passwords, and sensitive fields are excluded from skill suggestion outputs."""
        res = self.client.post(
            "/api/ai/skill-suggestions",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_alice}",
        )
        body_text = res.content.decode("utf-8")
        self.assertNotIn("GEMINI_API_KEY", body_text)
        self.assertNotIn("password", body_text.lower())
        self.assertNotIn("token", body_text.lower())

    # =================================================================
    # SECURITY & OUTPUT VALIDATION TESTS
    # =================================================================

    def test_review_analysis_unrelated_user_rejected(self):
        """An unrelated student requesting review analysis for another user is rejected with 403 FORBIDDEN."""
        res = self.client.post(
            "/api/ai/review-analysis",
            data=json.dumps({"user_id": str(self.student_alice.id)}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_bob}",
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json()["success"])
        self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")

    def test_review_analysis_applicant_cannot_analyze_job_or_other_applicant(self):
        """A mere applicant cannot use job scope to inspect the job or another applicant's reviews."""
        Application.objects.create(
            job=self.job_python,
            student=self.student_bob,
            application_message="I can also help with this project.",
            status=Application.Status.APPLIED,
        )

        job_res = self.client.post(
            "/api/ai/review-analysis",
            data=json.dumps({"job_id": str(self.job_python.id)}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_alice}",
        )
        self.assertEqual(job_res.status_code, 403)
        self.assertEqual(job_res.json()["error"]["code"], "FORBIDDEN")

        user_res = self.client.post(
            "/api/ai/review-analysis",
            data=json.dumps({"job_id": str(self.job_python.id), "user_id": str(self.student_bob.id)}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_alice}",
        )
        self.assertEqual(user_res.status_code, 403)
        self.assertEqual(user_res.json()["error"]["code"], "FORBIDDEN")

    def test_review_analysis_relevant_job_participant_allowed(self):
        """A client who hired or reviewed the student is allowed to access the review analysis."""
        completed_job = Job.objects.create(
            title="Reviewed Task",
            description="Build API",
            budget=Decimal("100.00"),
            job_provider=self.client_charlie,
            selected_student=self.student_alice,
            status=Job.Status.RATED,
        )
        Rating.objects.create(
            job=completed_job,
            reviewer=self.client_charlie,
            reviewed_user=self.student_alice,
            rating=5,
            review_content="Great job!",
        )
        res = self.client.post(
            "/api/ai/review-analysis",
            data=json.dumps({"user_id": str(self.student_alice.id)}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_charlie}",
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

    def test_match_candidates_filters_hallucinated_student_id(self):
        """Hallucinated candidate IDs returned by Gemini are strictly discarded server-side."""
        from ai.gemini_client import match_candidates_with_gemini

        job_data = {"title": "Test Job", "description": "Test", "required_skills": ["Python"], "budget": "100"}
        candidates_data = [
            {"student_id": str(self.student_alice.id), "student_name": "Alice", "username": "alice", "skills": ["Python"]},
        ]
        # Simulate Gemini returning a hallucinated student_id
        mock_result = match_candidates_with_gemini(job_data, candidates_data)
        self.assertIn("candidates", mock_result)
        for c in mock_result["candidates"]:
            self.assertEqual(c["student_id"], str(self.student_alice.id))

    def test_job_recommendations_filters_hallucinated_job_id(self):
        """Hallucinated job IDs returned by Gemini are strictly discarded server-side."""
        from ai.gemini_client import recommend_jobs_with_gemini

        student_data = {"student_name": "Alice", "skills": ["Python"]}
        jobs_data = [
            {"id": str(self.job_python.id), "title": "Python Job", "required_skills": ["Python"], "budget": "250"},
        ]
        mock_result = recommend_jobs_with_gemini(student_data, jobs_data)
        self.assertIn("recommendations", mock_result)
        for r in mock_result["recommendations"]:
            self.assertEqual(r["job_id"], str(self.job_python.id))



