import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0002_contactaccesslog"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="desired_area",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name="Desired area"),
        ),
        migrations.AddField(
            model_name="lead",
            name="desired_area_unit",
            field=models.CharField(blank=True, choices=[("sqft", "Sq ft"), ("sqyd", "Sq yd"), ("marla", "Marla"), ("kanal", "Kanal")], default="", max_length=12, verbose_name="Area unit"),
        ),
    ]
