from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="NotificationDelivery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("channel", models.CharField(choices=[("EMAIL", "Email"), ("SMS", "SMS")], max_length=16)),
                ("provider", models.CharField(max_length=32)),
                ("recipient", models.CharField(max_length=255)),
                ("subject", models.CharField(blank=True, max_length=255)),
                ("message", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("QUEUED", "Queued"), ("SENT", "Sent"), ("DELIVERED", "Delivered"), ("FAILED", "Failed")],
                        default="QUEUED",
                        max_length=16,
                    ),
                ),
                ("provider_message_id", models.CharField(blank=True, max_length=255)),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("last_error", models.TextField(blank=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddIndex(
            model_name="notificationdelivery",
            index=models.Index(fields=["channel", "provider", "status"], name="common_noti_channel_6facde_idx"),
        ),
        migrations.AddIndex(
            model_name="notificationdelivery",
            index=models.Index(fields=["provider_message_id"], name="common_noti_provide_2a3f1f_idx"),
        ),
        migrations.AddIndex(
            model_name="notificationdelivery",
            index=models.Index(fields=["created_at"], name="common_noti_created_e2415f_idx"),
        ),
    ]
