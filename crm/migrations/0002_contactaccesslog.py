import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("crm", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactAccessLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("viewed_lead", "Viewed lead"), ("exported_leads", "Exported leads")], db_index=True, max_length=20)),
                ("lead_pk", models.PositiveBigIntegerField(blank=True, db_index=True, null=True)),
                ("row_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("actor", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="contact_access_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Contact access log",
                "verbose_name_plural": "Contact access logs",
                "ordering": ["-created_at"],
            },
        ),
    ]
