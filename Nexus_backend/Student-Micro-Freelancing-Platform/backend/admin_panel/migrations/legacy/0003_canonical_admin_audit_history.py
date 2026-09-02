from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0005_canonical_user_contract"),
        ("admin_panel", "0002_alter_adminaction_action_type"),
    ]

    operations = [
        migrations.RenameModel(old_name="AdminAction", new_name="AdminActionHistory"),
        migrations.AlterModelTable(name="adminactionhistory", table="admin_action_history"),
        migrations.RenameField(model_name="adminactionhistory", old_name="admin", new_name="actor"),
        migrations.AlterField(model_name="adminactionhistory", name="actor", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="admin_actions", to=settings.AUTH_USER_MODEL)),
        migrations.RemoveField(model_name="adminactionhistory", name="action_type"),
        migrations.RemoveField(model_name="adminactionhistory", name="target_user"),
        migrations.RemoveField(model_name="adminactionhistory", name="reason"),
        migrations.AddField(model_name="adminactionhistory", name="entity_type", field=models.CharField(default="", max_length=32)),
        migrations.AddField(model_name="adminactionhistory", name="entity_id", field=models.UUIDField(null=True)),
        migrations.AddField(model_name="adminactionhistory", name="action", field=models.TextField(default="")),
        migrations.AddField(model_name="adminactionhistory", name="details", field=models.JSONField(default=dict)),
        migrations.AddIndex(model_name="adminactionhistory", index=models.Index(fields=["entity_type", "entity_id"], name="admin_action_history_entity_idx")),
    ]
