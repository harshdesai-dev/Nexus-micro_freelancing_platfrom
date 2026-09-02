import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Canonical NEXUS identity, compatible with Django authentication."""

    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        CLIENT = "CLIENT", "Client"
        ADMIN = "ADMIN", "Admin"

    class AccountStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        DISABLED = "DISABLED", "Disabled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, default="")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    account_status = models.CharField(
        max_length=10,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
    )
    email = models.EmailField(max_length=320, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.username} ({self.role})"
