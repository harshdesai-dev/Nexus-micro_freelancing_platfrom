import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from accounts.models import User


class StudentProfile(models.Model):
    # user_id is the profile primary key, matching the PostgreSQL contract.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile", primary_key=True)
    college = models.TextField(blank=True, default="")
    # Preserved current student-profile fields.
    course = models.CharField(max_length=200, blank=True, default="")
    year_of_study = models.CharField(max_length=20, blank=True, default="")
    bio = models.CharField(max_length=500, blank=True)
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)
    availability = models.TextField(blank=True, default="")
    # Canonical PostgreSQL-compatible profile fields. Skill remains normalized below.
    skills_data = models.JSONField(db_column="skills", default=list)
    portfolio = models.TextField(blank=True, default="")
    previous_work = models.TextField(blank=True, default="")
    profile_information = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_profiles"

    def clean(self):
        if self.user_id and self.user.role != User.Role.STUDENT:
            raise ValidationError("StudentProfile requires a STUDENT user.")

    def __str__(self):
        return f"{self.user.username} - Student Profile"


class Skill(models.Model):
    """Preserved normalized skill data; skills_data is the schema-compatible snapshot."""

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "student_skills"

    def __str__(self):
        return self.name


class PortfolioItem(models.Model):
    """Preserved item-level portfolio functionality absent from the SQL contract."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="portfolio_items")
    title = models.CharField(max_length=200)
    description = models.TextField()
    skills = models.TextField()
    project_url = models.URLField(blank=True, null=True)
    file = models.FileField(upload_to="portfolio/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    thumbnail = models.ImageField(upload_to="portfolio/thumbnails/", blank=True, null=True)
    is_visible = models.BooleanField(default=True)

    class Meta:
        db_table = "portfolio_items"

    def __str__(self):
        return self.title


class Verification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    student = models.ForeignKey(User, db_column="student_id", on_delete=models.RESTRICT, related_name="verifications")
    college_id_file = models.FileField(upload_to="verification/college_ids/", db_column="college_id_file_reference")
    status = models.CharField(max_length=10, db_column="verification_status", choices=Status.choices, default=Status.PENDING)
    admin_action = models.TextField(blank=True, default="")
    reviewed_by = models.ForeignKey(User, db_column="reviewed_by", on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_verifications")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    # Existing useful verification information retained outside the SQL minimum contract.
    college_name = models.CharField(max_length=255, blank=True, default="")
    course = models.CharField(max_length=255, blank=True, default="")
    academic_year = models.CharField(max_length=50, blank=True, default="")
    admin_reason = models.TextField(blank=True, default="")
    admin_internal_notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "verifications"
        indexes = [models.Index(fields=["status"], name="verifications_status_idx")]
        constraints = [
            models.UniqueConstraint(fields=["student"], condition=Q(status="PENDING"), name="one_pending_verification_per_student"),
        ]

    def clean(self):
        if self.student_id and self.student.role != User.Role.STUDENT:
            raise ValidationError("Verification requires a STUDENT reference.")

    @property
    def user(self):
        """Compatibility accessor for current pre-integration views."""
        return self.student

    def __str__(self):
        return f"{self.student.username} - {self.status}"


class VerificationHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verification = models.ForeignKey(Verification, on_delete=models.RESTRICT, related_name="history")
    previous_status = models.CharField(max_length=10, blank=True, default="")
    new_status = models.CharField(max_length=10)
    action = models.TextField()
    actor = models.ForeignKey(User, db_column="actor_id", on_delete=models.SET_NULL, null=True, blank=True, related_name="verification_history_actions")
    created_at = models.DateTimeField(auto_now_add=True)
    # Existing context retained.
    reason = models.TextField(blank=True, default="")

    class Meta:
        db_table = "verification_history"

    @property
    def status_from(self):
        return self.previous_status

    @property
    def status_to(self):
        return self.new_status

    @property
    def performed_by(self):
        return self.actor

    def __str__(self):
        return f"{self.verification} - {self.action}"
