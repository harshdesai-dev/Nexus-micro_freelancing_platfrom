import uuid

from django.db import models

from accounts.models import User


class AdminActionHistory(models.Model):
    """Generic, append-only administrative audit record."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="admin_actions")
    entity_type = models.CharField(max_length=32)
    entity_id = models.UUIDField()
    action = models.TextField()
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "admin_action_history"
        indexes = [models.Index(fields=["entity_type", "entity_id"], name="admin_history_entity")]


# Existing views import this symbol; the canonical model is AdminActionHistory.
AdminAction = AdminActionHistory
