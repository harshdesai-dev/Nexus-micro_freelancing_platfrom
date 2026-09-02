import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_user_account_status")]

    operations = [
        migrations.AlterModelTable(name="user", table="users"),
        migrations.AlterField(
            model_name="user",
            name="id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AddField(model_name="user", name="name", field=models.CharField(blank=True, default="", max_length=255)),
        migrations.AddField(model_name="user", name="created_at", field=models.DateTimeField(auto_now_add=True, null=True)),
        migrations.AddField(model_name="user", name="updated_at", field=models.DateTimeField(auto_now=True, null=True)),
        migrations.AlterField(model_name="user", name="email", field=models.EmailField(max_length=320, unique=True)),
        migrations.AlterField(
            model_name="user",
            name="account_status",
            field=models.CharField(choices=[("ACTIVE", "Active"), ("SUSPENDED", "Suspended"), ("DISABLED", "Disabled")], default="ACTIVE", max_length=10),
        ),
    ]
