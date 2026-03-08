from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="GeneratedReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("report_type", models.CharField(choices=[("INVENTORY_DAILY_SUMMARY", "Inventory Daily Summary")], max_length=64)),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[("GENERATING", "Generating"), ("GENERATED", "Generated"), ("FAILED", "Failed")],
                        default="GENERATING",
                        max_length=16,
                    ),
                ),
                ("row_count", models.PositiveIntegerField(default=0)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddIndex(
            model_name="generatedreport",
            index=models.Index(fields=["report_type", "period_start", "period_end"], name="reports_gen_report__74450f_idx"),
        ),
        migrations.AddIndex(
            model_name="generatedreport",
            index=models.Index(fields=["status", "created_at"], name="reports_gen_status_cacdbd_idx"),
        ),
    ]
