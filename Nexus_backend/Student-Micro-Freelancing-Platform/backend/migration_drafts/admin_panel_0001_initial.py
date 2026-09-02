"""
Draft: admin_panel 0001_initial migration (UUID-first)

Draft migration to create `admin_action_history`.
This is a draft for review only.
"""
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdminActionHistory',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('entity_type', models.CharField(max_length=32)),
                ('entity_id', models.UUIDField()),
                ('action', models.TextField()),
                ('details', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'admin_action_history'},
        ),
    ]
