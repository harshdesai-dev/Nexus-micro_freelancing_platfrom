import json
import uuid
from decimal import Decimal

from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User
from .models import Application, Job


class BaseMarketplaceTestCase(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student_user",
            email="student@example.com",
            password="password123",
            role=User.Role.STUDENT,
            name="Student User",
        )
        self.other_student = User.objects.create_user(
            username="other_student",
            email="other@example.com",
            password="password123",
            role=User.Role.STUDENT,
            name="Other Student",
        )
        self.provider = User.objects.create_user(
            username="provider_user",
            email="provider@example.com",
            password="password123",
            role=User.Role.CLIENT,
            name="Provider Client",
        )
        self.open_job = Job.objects.create(
            title="Python Automation Script",
            description="Write a Python script for CSV automation",
            required_skills=["Python", "Automation"],
            budget=Decimal("350.00"),
            job_provider=self.provider,
            status=Job.Status.POSTED,
        )

    def auth(self, user):
        return {"HTTP_AUTHORIZATION": f"Bearer {AccessToken.for_user(user)}"}


class JobsListViewTests(BaseMarketplaceTestCase):
    def test_authenticated_student_can_retrieve_available_jobs(self):
        response = self.client.get("/api/jobs", **self.auth(self.student))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        jobs = payload["data"]["jobs"]
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["id"], str(self.open_job.id))
        self.assertEqual(jobs[0]["title"], "Python Automation Script")
        self.assertEqual(jobs[0]["required_skills"], ["Python", "Automation"])
        self.assertEqual(jobs[0]["job_provider"]["name"], "Provider Client")

    def test_only_open_jobs_are_returned(self):
        # Job in APPLICATIONS status should be listed
        job_apps = Job.objects.create(
            title="Applications Open Job",
            description="Actively accepting applications",
            budget=Decimal("200.00"),
            job_provider=self.provider,
            status=Job.Status.APPLICATIONS,
        )
        # Completed / In-progress jobs should NOT be listed in public open jobs
        Job.objects.create(
            title="In Progress Job",
            description="Already in progress",
            budget=Decimal("500.00"),
            job_provider=self.provider,
            status=Job.Status.IN_PROGRESS,
        )
        Job.objects.create(
            title="Completed Job",
            description="Already done",
            budget=Decimal("100.00"),
            job_provider=self.provider,
            status=Job.Status.COMPLETED,
        )
        response = self.client.get("/api/jobs", **self.auth(self.student))
        self.assertEqual(response.status_code, 200)
        jobs = response.json()["data"]["jobs"]
        job_ids = [j["id"] for j in jobs]
        self.assertIn(str(self.open_job.id), job_ids)
        self.assertIn(str(job_apps.id), job_ids)
        self.assertEqual(len(jobs), 2)

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.get("/api/jobs")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "UNAUTHORIZED")


class JobDetailViewTests(BaseMarketplaceTestCase):
    def test_retrieve_job_by_valid_uuid(self):
        response = self.client.get(f"/api/jobs/{self.open_job.id}", **self.auth(self.student))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        job = payload["data"]["job"]
        self.assertEqual(job["id"], str(self.open_job.id))
        self.assertEqual(job["title"], "Python Automation Script")
        self.assertEqual(job["budget"], "350.00")
        self.assertEqual(job["job_provider"]["username"], "provider_user")

    def test_nonexistent_job_uuid_returns_404(self):
        random_id = uuid.uuid4()
        response = self.client.get(f"/api/jobs/{random_id}", **self.auth(self.student))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")

    def test_unauthenticated_detail_request_is_rejected(self):
        response = self.client.get(f"/api/jobs/{self.open_job.id}")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "UNAUTHORIZED")


class ApplyJobViewTests(BaseMarketplaceTestCase):
    def test_valid_student_can_apply(self):
        payload = {
            "application_message": "I have experience with Python and can complete this in 2 days.",
            "expected_completion": "2026-09-10",
            "application_information": {"skills": ["Python"]},
        }
        response = self.client.post(
            f"/api/jobs/{self.open_job.id}/applications",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth(self.student),
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()["data"]["application"]
        self.assertEqual(data["status"], "APPLIED")
        self.assertTrue(Application.objects.filter(job=self.open_job, student=self.student).exists())

    def test_successful_application_changes_job_state_to_applications(self):
        self.assertEqual(self.open_job.status, Job.Status.POSTED)
        self.client.post(
            f"/api/jobs/{self.open_job.id}/applications",
            data=json.dumps({"application_message": "Ready to work"}),
            content_type="application/json",
            **self.auth(self.student),
        )
        self.open_job.refresh_from_db()
        self.assertEqual(self.open_job.status, Job.Status.APPLICATIONS)

    def test_non_student_is_rejected(self):
        response = self.client.post(
            f"/api/jobs/{self.open_job.id}/applications",
            data=json.dumps({"application_message": "I am a client"}),
            content_type="application/json",
            **self.auth(self.provider),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")

    def test_unauthenticated_apply_is_rejected(self):
        response = self.client.post(
            f"/api/jobs/{self.open_job.id}/applications",
            data=json.dumps({"application_message": "No auth"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "UNAUTHORIZED")

    def test_provider_cannot_apply_to_own_job(self):
        # Create a job provided by a student user
        student_job = Job.objects.create(
            title="Student-provided Job",
            description="Test",
            budget=Decimal("50.00"),
            job_provider=self.student,
            status=Job.Status.POSTED,
        )
        response = self.client.post(
            f"/api/jobs/{student_job.id}/applications",
            data=json.dumps({"application_message": "Applying to own job"}),
            content_type="application/json",
            **self.auth(self.student),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")

    def test_duplicate_application_is_rejected(self):
        Application.objects.create(
            job=self.open_job,
            student=self.student,
            application_message="First application",
        )
        response = self.client.post(
            f"/api/jobs/{self.open_job.id}/applications",
            data=json.dumps({"application_message": "Second application attempt"}),
            content_type="application/json",
            **self.auth(self.student),
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "APPLICATION_EXISTS")

    def test_apply_to_closed_job_is_rejected(self):
        closed_job = Job.objects.create(
            title="Closed Job",
            description="Completed job",
            budget=Decimal("100.00"),
            job_provider=self.provider,
            status=Job.Status.COMPLETED,
        )
        response = self.client.post(
            f"/api/jobs/{closed_job.id}/applications",
            data=json.dumps({"application_message": "Applying to closed job"}),
            content_type="application/json",
            **self.auth(self.student),
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "INVALID_STATE")


class MyApplicationsViewTests(BaseMarketplaceTestCase):
    def setUp(self):
        super().setUp()
        self.application = Application.objects.create(
            job=self.open_job,
            student=self.student,
            application_message="I can help",
        )

    def test_student_receives_only_own_applications_with_job_summary(self):
        other_job = Job.objects.create(
            title="Other job",
            description="Other",
            budget=Decimal("50.00"),
            job_provider=self.provider,
        )
        Application.objects.create(job=other_job, student=self.other_student)
        response = self.client.get("/api/applications/mine", **self.auth(self.student))
        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]["applications"]
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["id"], str(self.application.id))
        self.assertEqual(payload[0]["job"]["id"], str(self.open_job.id))
        self.assertEqual(payload[0]["job"]["title"], "Python Automation Script")

    def test_non_student_cannot_list_student_applications(self):
        response = self.client.get("/api/applications/mine", **self.auth(self.provider))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.get("/api/applications/mine")
        self.assertEqual(response.status_code, 401)


class ApplicationDetailViewTests(BaseMarketplaceTestCase):
    def setUp(self):
        super().setUp()
        self.application = Application.objects.create(
            job=self.open_job,
            student=self.student,
            application_message="Cover letter text",
            application_information={"skills": ["Python"]},
        )

    def test_student_can_retrieve_own_application_detail(self):
        response = self.client.get(f"/api/applications/{self.application.id}", **self.auth(self.student))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        app = payload["data"]["application"]
        self.assertEqual(app["id"], str(self.application.id))
        self.assertEqual(app["status"], "APPLIED")
        self.assertEqual(app["application_message"], "Cover letter text")
        self.assertEqual(app["job"]["id"], str(self.open_job.id))
        self.assertEqual(app["job"]["title"], "Python Automation Script")

    def test_student_cannot_retrieve_other_student_application(self):
        response = self.client.get(f"/api/applications/{self.application.id}", **self.auth(self.other_student))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")

    def test_non_student_cannot_retrieve_application_detail(self):
        response = self.client.get(f"/api/applications/{self.application.id}", **self.auth(self.provider))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.get(f"/api/applications/{self.application.id}")
        self.assertEqual(response.status_code, 401)

    def test_nonexistent_application_uuid_returns_404(self):
        random_id = uuid.uuid4()
        response = self.client.get(f"/api/applications/{random_id}", **self.auth(self.student))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")


class CreateJobViewTests(BaseMarketplaceTestCase):
    def test_client_can_create_job(self):
        payload = {
            "title": "Build a React Native Component",
            "description": "Create a reusable card component with unit tests.",
            "required_skills": ["React Native", "TypeScript"],
            "budget": "450.00",
            "deadline": "2026-10-15T18:00:00Z",
        }
        response = self.client.post(
            "/api/jobs",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth(self.provider),
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()["data"]["job"]
        self.assertEqual(data["title"], "Build a React Native Component")
        self.assertEqual(data["budget"], "450.00")
        self.assertEqual(data["job_state"], "POSTED")
        self.assertEqual(data["job_provider"]["id"], str(self.provider.id))
        self.assertTrue(uuid.UUID(data["id"]))

    def test_unauthenticated_job_creation_rejected(self):
        response = self.client.post(
            "/api/jobs",
            data=json.dumps({"title": "Test", "description": "Desc", "budget": "100"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "UNAUTHORIZED")

    def test_student_cannot_create_job(self):
        response = self.client.post(
            "/api/jobs",
            data=json.dumps({"title": "Student Job", "description": "Desc", "budget": "100"}),
            content_type="application/json",
            **self.auth(self.student),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")

    def test_job_creation_missing_required_fields(self):
        response = self.client.post(
            "/api/jobs",
            data=json.dumps({"title": "Incomplete Job"}),
            content_type="application/json",
            **self.auth(self.provider),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")

    def test_job_creation_invalid_budget(self):
        response = self.client.post(
            "/api/jobs",
            data=json.dumps({"title": "Bad Budget", "description": "Desc", "budget": "invalid_num"}),
            content_type="application/json",
            **self.auth(self.provider),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")


class MyJobsViewTests(BaseMarketplaceTestCase):
    def test_client_can_list_only_own_jobs(self):
        other_provider = User.objects.create_user(
            username="other_provider",
            email="other_provider@example.com",
            password="password123",
            role=User.Role.CLIENT,
            name="Other Client",
        )
        Job.objects.create(
            title="Other Client Job",
            description="Created by another client",
            budget=Decimal("700.00"),
            job_provider=other_provider,
        )
        response = self.client.get("/api/jobs/mine", **self.auth(self.provider))
        self.assertEqual(response.status_code, 200)
        jobs = response.json()["data"]["jobs"]
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["id"], str(self.open_job.id))
        self.assertEqual(jobs[0]["title"], "Python Automation Script")

    def test_student_cannot_access_my_jobs(self):
        response = self.client.get("/api/jobs/mine", **self.auth(self.student))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")

    def test_unauthenticated_my_jobs_rejected(self):
        response = self.client.get("/api/jobs/mine")
        self.assertEqual(response.status_code, 401)


class ClientApplicationsViewTests(BaseMarketplaceTestCase):
    def setUp(self):
        super().setUp()
        self.application = Application.objects.create(
            job=self.open_job,
            student=self.student,
            application_message="Experienced with Python automation.",
            application_information={"skills": ["Python", "Automation"]},
        )
        self.other_provider = User.objects.create_user(
            username="other_client_user",
            email="other_client@example.com",
            password="password123",
            role=User.Role.CLIENT,
            name="Other Provider",
        )

    def test_job_owner_can_view_applications_for_job(self):
        response = self.client.get(f"/api/jobs/{self.open_job.id}/applications", **self.auth(self.provider))
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        apps = data["applications"]
        self.assertEqual(len(apps), 1)
        self.assertEqual(apps[0]["id"], str(self.application.id))
        self.assertEqual(apps[0]["student"]["name"], "Student User")
        self.assertEqual(apps[0]["application_message"], "Experienced with Python automation.")
        self.assertEqual(apps[0]["status"], "APPLIED")
        self.assertEqual(data["job"]["id"], str(self.open_job.id))

    def test_non_owner_client_cannot_view_applications(self):
        response = self.client.get(f"/api/jobs/{self.open_job.id}/applications", **self.auth(self.other_provider))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")

    def test_student_cannot_view_client_applications(self):
        response = self.client.get(f"/api/jobs/{self.open_job.id}/applications", **self.auth(self.student))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")

    def test_unauthenticated_applications_view_rejected(self):
        response = self.client.get(f"/api/jobs/{self.open_job.id}/applications")
        self.assertEqual(response.status_code, 401)

    def test_applications_for_nonexistent_job_returns_404(self):
        random_id = uuid.uuid4()
        response = self.client.get(f"/api/jobs/{random_id}/applications", **self.auth(self.provider))
        self.assertEqual(response.status_code, 404)


class SelectStudentViewTests(BaseMarketplaceTestCase):
    def setUp(self):
        super().setUp()
        self.application = Application.objects.create(
            job=self.open_job,
            student=self.student,
            application_message="Pick me for this job",
        )
        self.other_provider = User.objects.create_user(
            username="another_client",
            email="another_client@example.com",
            password="password123",
            role=User.Role.CLIENT,
            name="Another Client",
        )

    def test_valid_student_selection(self):
        response = self.client.post(
            f"/api/jobs/{self.open_job.id}/select",
            data=json.dumps({"application_id": str(self.application.id)}),
            content_type="application/json",
            **self.auth(self.provider),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["job"]["job_state"], "STUDENT_SELECTED")
        self.assertEqual(data["job"]["selected_student"]["id"], str(self.student.id))
        self.open_job.refresh_from_db()
        self.application.refresh_from_db()
        self.assertEqual(self.open_job.status, Job.Status.STUDENT_SELECTED)
        self.assertEqual(self.open_job.selected_student_id, self.student.id)
        self.assertEqual(self.application.status, Application.Status.SELECTED)

    def test_non_owner_client_cannot_select(self):
        response = self.client.post(
            f"/api/jobs/{self.open_job.id}/select",
            data=json.dumps({"application_id": str(self.application.id)}),
            content_type="application/json",
            **self.auth(self.other_provider),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")

    def test_student_cannot_select_student(self):
        response = self.client.post(
            f"/api/jobs/{self.open_job.id}/select",
            data=json.dumps({"application_id": str(self.application.id)}),
            content_type="application/json",
            **self.auth(self.student),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")

    def test_cannot_select_for_completed_job(self):
        self.open_job.status = Job.Status.COMPLETED
        self.open_job.save()
        response = self.client.post(
            f"/api/jobs/{self.open_job.id}/select",
            data=json.dumps({"application_id": str(self.application.id)}),
            content_type="application/json",
            **self.auth(self.provider),
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "INVALID_STATE")

    def test_cannot_select_application_of_another_job(self):
        other_job = Job.objects.create(
            title="Other Job",
            description="Other description",
            budget=Decimal("150.00"),
            job_provider=self.provider,
        )
        other_app = Application.objects.create(
            job=other_job,
            student=self.other_student,
        )
        response = self.client.post(
            f"/api/jobs/{self.open_job.id}/select",
            data=json.dumps({"application_id": str(other_app.id)}),
            content_type="application/json",
            **self.auth(self.provider),
        )
        self.assertEqual(response.status_code, 404)

    def test_cannot_select_already_selected_student(self):
        self.application.status = Application.Status.SELECTED
        self.application.save()
        self.open_job.selected_student = self.student
        self.open_job.status = Job.Status.STUDENT_SELECTED
        self.open_job.save()

        other_app = Application.objects.create(
            job=self.open_job,
            student=self.other_student,
        )
        response = self.client.post(
            f"/api/jobs/{self.open_job.id}/select",
            data=json.dumps({"application_id": str(other_app.id)}),
            content_type="application/json",
            **self.auth(self.provider),
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "INVALID_STATE")

    def test_missing_application_id_returns_validation_error(self):
        response = self.client.post(
            f"/api/jobs/{self.open_job.id}/select",
            data=json.dumps({}),
            content_type="application/json",
            **self.auth(self.provider),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
