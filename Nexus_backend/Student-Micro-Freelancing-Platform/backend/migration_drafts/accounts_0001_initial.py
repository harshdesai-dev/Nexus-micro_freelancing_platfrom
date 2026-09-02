"""
Draft: accounts 0001_initial migration (UUID-first)

This is a draft for review only. It should be turned into
`backend/accounts/migrations/0001_initial.py` after review/approval.
Do NOT apply this file directly.
"""
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('username', models.CharField(max_length=150)),
                ('password', models.CharField(max_length=128)),
                ('name', models.CharField(max_length=255, blank=True, default='')),
                ('email', models.EmailField(max_length=320, unique=True)),
                ('role', models.CharField(max_length=10)),
                ('account_status', models.CharField(max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'users'},
        ),
    ]
