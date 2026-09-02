import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from accounts.models import User


class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client_profile", primary_key=True)
    profile_information = models.JSONField(default=dict, blank=True)
    reputation = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "client_profiles"
        constraints = [models.CheckConstraint(condition=Q(reputation__gte=0) & Q(reputation__lte=5), name="client_reputation_between_zero_and_five")]

    def clean(self):
        if self.user_id and self.user.role != User.Role.CLIENT:
            raise ValidationError("ClientProfile requires a CLIENT user.")


class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        POSTED = "POSTED", "Posted"
        APPLICATIONS = "APPLICATIONS", "Applications"
        STUDENT_SELECTED = "STUDENT_SELECTED", "Student Selected"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        WORK_SUBMITTED = "WORK_SUBMITTED", "Work Submitted"
        PAYMENT = "PAYMENT", "Payment"
        COMPLETED = "COMPLETED", "Completed"
        RATED = "RATED", "Rated"

    title = models.CharField(max_length=255)
    description = models.TextField()
    required_skills = models.JSONField(default=list, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    deadline = models.DateTimeField(null=True, blank=True)
    reference_files = models.JSONField(default=list, blank=True)
    job_provider = models.ForeignKey(User, db_column="job_provider", on_delete=models.RESTRICT, related_name="posted_jobs")
    selected_student = models.ForeignKey(User, db_column="selected_student", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_jobs")
    status = models.CharField(max_length=20, db_column="job_state", choices=Status.choices, default=Status.POSTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "jobs"
        indexes = [models.Index(fields=["job_provider"], name="jobs_provider_idx")]
        constraints = [models.CheckConstraint(condition=Q(budget__gte=0), name="job_budget_non_negative")]

    def clean(self):
        if self.job_provider_id and self.job_provider.role not in (User.Role.STUDENT, User.Role.CLIENT):
            raise ValidationError("Only STUDENT or CLIENT users may provide marketplace jobs.")
        if self.selected_student_id and self.selected_student.role != User.Role.STUDENT:
            raise ValidationError("selected_student must be a STUDENT user.")

    @property
    def provider(self):
        """Compatibility accessor for pre-integration views."""
        return self.job_provider


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        APPLIED = "APPLIED", "Applied"
        SELECTED = "SELECTED", "Selected"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    student = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="job_applications")
    application_information = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, db_column="application_status", choices=Status.choices, default=Status.APPLIED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Preserved current application data pending API-contract migration.
    application_message = models.TextField(blank=True, default="")
    expected_completion = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "applications"
        indexes = [models.Index(fields=["student"], name="applications_student_idx")]
        constraints = [
            models.UniqueConstraint(fields=["job", "student"], name="one_application_per_student_per_job"),
            models.UniqueConstraint(fields=["job"], condition=Q(status="SELECTED"), name="one_selected_application_per_job"),
        ]

    def clean(self):
        if self.student_id and self.student.role != User.Role.STUDENT:
            raise ValidationError("Application requires a STUDENT reference.")


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, db_column="sender", on_delete=models.RESTRICT, related_name="sent_messages")
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
        indexes = [models.Index(fields=["job"], name="messages_job_idx")]
        constraints = [models.CheckConstraint(condition=~Q(message=""), name="message_not_empty")]


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="work_submissions")
    submitted_work = models.JSONField(default=list, blank=True)
    submission_information = models.JSONField(default=dict, blank=True)
    submission_status = models.CharField(max_length=10, choices=Status.choices, default=Status.SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "submissions"
        indexes = [models.Index(fields=["job"], name="submissions_job_idx")]

    def clean(self):
        if self.student_id and self.student.role != User.Role.STUDENT:
            raise ValidationError("Submission requires a STUDENT reference.")


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    job = models.ForeignKey(Job, on_delete=models.RESTRICT, related_name="payments")
    payer = models.ForeignKey(User, db_column="payer", on_delete=models.RESTRICT, related_name="payments_made")
    recipient = models.ForeignKey(User, db_column="recipient", on_delete=models.RESTRICT, related_name="payments_received")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    platform_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transaction_status = models.CharField(max_length=10, db_column="transaction_state", choices=Status.choices, default=Status.PENDING)
    transaction_reference = models.TextField(unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        constraints = [
            models.CheckConstraint(condition=Q(amount__gte=0), name="payment_amount_non_negative"),
            models.CheckConstraint(condition=Q(platform_commission__gte=0) & Q(platform_commission__lte=models.F("amount")), name="payment_commission_in_range"),
            models.CheckConstraint(condition=~Q(payer=models.F("recipient")), name="payment_payer_not_recipient"),
        ]


class Rating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="ratings")
    reviewer = models.ForeignKey(User, db_column="reviewer", on_delete=models.RESTRICT, related_name="given_ratings")
    reviewed_user = models.ForeignKey(User, db_column="reviewed_user", on_delete=models.RESTRICT, related_name="received_ratings")
    rating = models.SmallIntegerField()
    review_content = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ratings"
        constraints = [
            models.CheckConstraint(condition=Q(rating__gte=1) & Q(rating__lte=5), name="rating_between_one_and_five"),
            models.CheckConstraint(condition=~Q(reviewer=models.F("reviewed_user")), name="rating_reviewer_not_reviewed"),
            models.UniqueConstraint(fields=["job", "reviewer", "reviewed_user"], name="one_rating_per_reviewer_per_job"),
        ]


class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        RESOLVED = "RESOLVED", "Resolved"
        DISMISSED = "DISMISSED", "Dismissed"

    reporter = models.ForeignKey(User, db_column="reporter", on_delete=models.RESTRICT, related_name="reports_filed")
    reported_user = models.ForeignKey(User, db_column="reported_user", on_delete=models.RESTRICT, null=True, blank=True, related_name="reports_received")
    reported_job = models.ForeignKey(Job, db_column="reported_job", on_delete=models.RESTRICT, null=True, blank=True, related_name="reports")
    related_job = models.ForeignKey(Job, db_column="related_job", on_delete=models.RESTRICT, null=True, blank=True, related_name="related_reports")
    reason = models.CharField(max_length=255)
    details = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    admin_action = models.TextField(blank=True, default="")
    reviewed_by = models.ForeignKey(User, db_column="reviewed_by", on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_reports")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reports"
        indexes = [models.Index(fields=["status"], name="reports_status_idx")]
        constraints = [models.CheckConstraint(condition=Q(reported_user__isnull=False) | Q(reported_job__isnull=False) | Q(related_job__isnull=False), name="report_requires_target")]


class Dispute(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        RESOLVED = "RESOLVED", "Resolved"
        DISMISSED = "DISMISSED", "Dismissed"

    job = models.ForeignKey(Job, on_delete=models.RESTRICT, related_name="disputes")
    raised_by = models.ForeignKey(User, db_column="raised_by", on_delete=models.RESTRICT, related_name="raised_disputes")
    issue = models.CharField(max_length=255)
    details = models.TextField()
    admin_handling = models.TextField(blank=True, default="")
    resolution = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    reviewed_by = models.ForeignKey(User, db_column="reviewed_by", on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_disputes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    involved_users = models.ManyToManyField(User, through="DisputeParticipant", related_name="disputes")

    class Meta:
        db_table = "disputes"
        indexes = [models.Index(fields=["status"], name="disputes_status_idx")]


class DisputeParticipant(models.Model):
    dispute = models.ForeignKey(Dispute, on_delete=models.RESTRICT, db_column="dispute_id")
    user = models.ForeignKey(User, on_delete=models.RESTRICT, db_column="user_id")

    class Meta:
        db_table = "dispute_users"
        constraints = [models.UniqueConstraint(fields=["dispute", "user"], name="unique_dispute_participant")]


# Compatibility aliases prevent import errors until the API layer is migrated.
JobApplication = Application
Communication = Message
WorkSubmission = Submission
Reporting = Report
