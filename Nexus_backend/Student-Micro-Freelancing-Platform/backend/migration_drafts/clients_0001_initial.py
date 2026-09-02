"""
Draft: clients 0001_initial migration (UUID-first)

Draft migration to create `client_profiles`, `jobs`, `applications`, `messages`, `submissions`,
`payments`, `ratings`, `reports`, `disputes`, `dispute_users`.
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
            name='ClientProfile',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, to='accounts.user', related_name='client_profile')),
                ('profile_information', models.JSONField(default=dict)),
                ('reputation', models.DecimalField(max_digits=3, decimal_places=2, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'client_profiles'},
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
            ],
            options={'db_table': 'jobs'},
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
            ],
            options={'db_table': 'applications'},
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
            ],
            options={'db_table': 'messages'},
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
            ],
            options={'db_table': 'submissions'},
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
            ],
            options={'db_table': 'payments'},
        ),
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
            ],
            options={'db_table': 'ratings'},
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
            ],
            options={'db_table': 'reports'},
        ),
        migrations.CreateModel(
            name='Dispute',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
            ],
            options={'db_table': 'disputes'},
        ),
        migrations.CreateModel(
            name='DisputeUser',
            fields=[
                ('dispute', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='clients.dispute')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='accounts.user')),
            ],
            options={'db_table': 'dispute_users'},
        ),
    ]
