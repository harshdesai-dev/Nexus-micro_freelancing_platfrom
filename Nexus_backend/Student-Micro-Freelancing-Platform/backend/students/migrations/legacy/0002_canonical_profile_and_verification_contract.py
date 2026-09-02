from django.conf import settings
from django.db import migrations, models
from django.db.models import Q
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("students", "0001_initial"),
        ("accounts", "0005_canonical_user_contract"),
    ]

    operations = [
        migrations.AlterModelTable(name="studentprofile", table="student_profiles"),
        migrations.AlterModelTable(name="skill", table="student_skills"),
        migrations.AlterModelTable(name="portfolioitem", table="portfolio_items"),
        migrations.AlterModelTable(name="verification", table="verifications"),
        migrations.AlterModelTable(name="verificationhistory", table="verification_history"),
        migrations.RemoveField(model_name="studentprofile", name="id"),
        migrations.AlterField(model_name="studentprofile", name="user", field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name="student_profile", serialize=False, to=settings.AUTH_USER_MODEL)),
        migrations.AlterField(model_name="studentprofile", name="college", field=models.TextField(blank=True, default="")),
        migrations.AlterField(model_name="studentprofile", name="course", field=models.CharField(blank=True, default="", max_length=200)),
        migrations.AlterField(model_name="studentprofile", name="year_of_study", field=models.CharField(blank=True, default="", max_length=20)),
        migrations.AlterField(model_name="studentprofile", name="availability", field=models.TextField(blank=True, default="")),
        migrations.AddField(model_name="studentprofile", name="skills_data", field=models.JSONField(db_column="skills", default=list)),
        migrations.AddField(model_name="studentprofile", name="portfolio", field=models.TextField(blank=True, default="")),
        migrations.AddField(model_name="studentprofile", name="previous_work", field=models.TextField(blank=True, default="")),
        migrations.AddField(model_name="studentprofile", name="profile_information", field=models.JSONField(default=dict)),
        migrations.AddField(model_name="studentprofile", name="created_at", field=models.DateTimeField(auto_now_add=True, null=True)),
        migrations.AddField(model_name="studentprofile", name="updated_at", field=models.DateTimeField(auto_now=True, null=True)),
        migrations.RenameField(model_name="verification", old_name="user", new_name="student"),
        migrations.AlterField(model_name="verification", name="student", field=models.ForeignKey(db_column="student_id", on_delete=django.db.models.deletion.RESTRICT, related_name="verifications", to=settings.AUTH_USER_MODEL)),
        migrations.AlterField(model_name="verification", name="college_id_file", field=models.FileField(db_column="college_id_file_reference", upload_to="verification/college_ids/")),
        migrations.AlterField(model_name="verification", name="reviewed_by", field=models.ForeignKey(blank=True, db_column="reviewed_by", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_verifications", to=settings.AUTH_USER_MODEL)),
        migrations.AlterField(model_name="verification", name="status", field=models.CharField(choices=[("PENDING", "Pending"), ("VERIFIED", "Verified"), ("REJECTED", "Rejected")], db_column="verification_status", default="PENDING", max_length=10)),
        migrations.RemoveField(model_name="verification", name="submitted_at"),
        migrations.AlterField(model_name="verification", name="admin_action", field=models.TextField(blank=True, default="")),
        migrations.AlterField(model_name="verification", name="college_name", field=models.CharField(blank=True, default="", max_length=255)),
        migrations.AlterField(model_name="verification", name="course", field=models.CharField(blank=True, default="", max_length=255)),
        migrations.AlterField(model_name="verification", name="academic_year", field=models.CharField(blank=True, default="", max_length=50)),
        migrations.AlterField(model_name="verification", name="admin_reason", field=models.TextField(blank=True, default="")),
        migrations.AlterField(model_name="verification", name="admin_internal_notes", field=models.TextField(blank=True, default="")),
        migrations.AddConstraint(model_name="verification", constraint=models.UniqueConstraint(condition=Q(status="PENDING"), fields=("student",), name="one_pending_verification_per_student")),
        migrations.AddIndex(model_name="verification", index=models.Index(fields=["status"], name="verifications_status_idx")),
        migrations.RenameField(model_name="verificationhistory", old_name="status_from", new_name="previous_status"),
        migrations.RenameField(model_name="verificationhistory", old_name="status_to", new_name="new_status"),
        migrations.RenameField(model_name="verificationhistory", old_name="performed_by", new_name="actor"),
        migrations.AlterField(model_name="verificationhistory", name="verification", field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name="history", to="students.verification")),
        migrations.AlterField(model_name="verificationhistory", name="actor", field=models.ForeignKey(blank=True, db_column="actor_id", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="verification_history_actions", to=settings.AUTH_USER_MODEL)),
        migrations.AlterField(model_name="verificationhistory", name="action", field=models.TextField()),
        migrations.AlterField(model_name="verificationhistory", name="previous_status", field=models.CharField(blank=True, default="", max_length=10)),
        migrations.AlterField(model_name="verificationhistory", name="new_status", field=models.CharField(max_length=10)),
        migrations.AlterField(model_name="verificationhistory", name="reason", field=models.TextField(blank=True, default="")),
    ]
