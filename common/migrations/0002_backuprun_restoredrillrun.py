from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BackupRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[("RUNNING", "Running"), ("SUCCESS", "Success"), ("FAILED", "Failed")],
                        default="RUNNING",
                        max_length=16,
                    ),
                ),
                ("backup_file", models.CharField(blank=True, max_length=512)),
                ("checksum_sha256", models.CharField(blank=True, max_length=64)),
                ("backup_size_bytes", models.BigIntegerField(default=0)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="RestoreDrillRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[("RUNNING", "Running"), ("SUCCESS", "Success"), ("FAILED", "Failed")],
                        default="RUNNING",
                        max_length=16,
                    ),
                ),
                ("details", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                (
                    "backup_run",
                    models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name="restore_drills", to="common.backuprun"),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="backuprun",
            index=models.Index(fields=["status", "started_at"], name="common_back_status_200bae_idx"),
        ),
        migrations.AddIndex(
            model_name="backuprun",
            index=models.Index(fields=["started_at"], name="common_back_started_55d507_idx"),
        ),
        migrations.AddIndex(
            model_name="restoredrillrun",
            index=models.Index(fields=["status", "started_at"], name="common_rest_status_2e605a_idx"),
        ),
        migrations.AddIndex(
            model_name="restoredrillrun",
            index=models.Index(fields=["started_at"], name="common_rest_started_d4f24e_idx"),
        ),
    ]
