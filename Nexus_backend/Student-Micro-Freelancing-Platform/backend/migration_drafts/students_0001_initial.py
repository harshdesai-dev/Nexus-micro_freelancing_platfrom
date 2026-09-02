"""
Draft: students 0001_initial migration (UUID-first)

Draft migration to create `student_profiles`, `verifications`, and `verification_history`.
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
            name='StudentProfile',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, to='accounts.user', related_name='student_profile')),
                ('college', models.TextField(blank=True, default='')),
                ('skills', models.JSONField(default=list)),
                ('portfolio', models.TextField(blank=True, default='')),
                ('previous_work', models.TextField(blank=True, default='')),
                ('profile_information', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'student_profiles'},
        ),
        migrations.CreateModel(
            name='Verification',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
            ],
            options={'db_table': 'verifications'},
        ),
        migrations.CreateModel(
            name='VerificationHistory',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
            ],
            options={'db_table': 'verification_history'},
        ),
    ]
