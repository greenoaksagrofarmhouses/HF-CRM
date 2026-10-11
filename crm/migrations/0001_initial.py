# Initial schema for Hartus Floare. Generated to match crm/models.py.
from decimal import Decimal
import django.core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Lead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("full_name", models.CharField(db_index=True, max_length=160)),
                ("company", models.CharField(blank=True, max_length=160)),
                ("phone", models.CharField(db_index=True, max_length=32)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("source", models.CharField(choices=[("website", "Website"), ("whatsapp", "WhatsApp"), ("facebook", "Facebook / Instagram"), ("portal", "Property portal"), ("referral", "Referral"), ("walk_in", "Walk-in"), ("cold_call", "Cold call"), ("other", "Other")], db_index=True, default="other", max_length=20)),
                ("status", models.CharField(choices=[("new", "New"), ("contacted", "Contacted"), ("qualified", "Qualified"), ("viewing", "Viewing scheduled"), ("negotiation", "Negotiation"), ("won", "Won"), ("lost", "Lost")], db_index=True, default="new", max_length=20)),
                ("interest", models.CharField(choices=[("buy", "Buying"), ("rent", "Renting"), ("sell", "Selling"), ("invest", "Investment")], default="buy", max_length=12)),
                ("property_type", models.CharField(blank=True, help_text="Apartment, house, plot, commercial, etc.", max_length=40)),
                ("budget_min", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ("budget_max", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ("preferred_location", models.CharField(blank=True, max_length=180)),
                ("priority", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")], db_index=True, default="medium", max_length=10)),
                ("next_follow_up", models.DateField(blank=True, db_index=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_leads", to=settings.AUTH_USER_MODEL)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_leads", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Lead",
                "verbose_name_plural": "Leads",
                "ordering": ["-updated_at"],
                "indexes": [models.Index(fields=["status", "priority"], name="crm_lead_status_prio_idx"), models.Index(fields=["assigned_to", "next_follow_up"], name="crm_lead_assign_follow_idx")],
            },
        ),
        migrations.CreateModel(
            name="Property",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(db_index=True, max_length=180)),
                ("code", models.CharField(blank=True, help_text="Leave blank to generate a reference code.", max_length=24, unique=True)),
                ("property_type", models.CharField(choices=[("house", "House"), ("apartment", "Apartment"), ("plot", "Plot"), ("commercial", "Commercial"), ("office", "Office"), ("farmhouse", "Farmhouse"), ("other", "Other")], default="house", max_length=20)),
                ("listing_type", models.CharField(choices=[("sale", "For sale"), ("rent", "For rent")], default="sale", max_length=10)),
                ("status", models.CharField(choices=[("available", "Available"), ("reserved", "Reserved"), ("sold", "Sold"), ("rented", "Rented"), ("off_market", "Off market")], db_index=True, default="available", max_length=15)),
                ("price", models.DecimalField(decimal_places=2, max_digits=15, validators=[django.core.validators.MinValueValidator(0)])),
                ("bedrooms", models.PositiveSmallIntegerField(default=0)),
                ("bathrooms", models.PositiveSmallIntegerField(default=0)),
                ("area_value", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ("area_unit", models.CharField(choices=[("sqft", "sq ft"), ("sqyd", "sq yd"), ("marla", "marla"), ("kanal", "kanal")], default="marla", max_length=12)),
                ("city", models.CharField(db_index=True, default="Lahore", max_length=80)),
                ("neighborhood", models.CharField(blank=True, db_index=True, max_length=140)),
                ("address", models.CharField(blank=True, max_length=240)),
                ("owner_name", models.CharField(blank=True, max_length=160)),
                ("owner_phone", models.CharField(blank=True, max_length=32)),
                ("description", models.TextField(blank=True)),
                ("featured", models.BooleanField(default=False)),
                ("assigned_agent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="managed_properties", to=settings.AUTH_USER_MODEL)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_properties", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-featured", "-created_at"],
                "indexes": [models.Index(fields=["city", "neighborhood", "status"], name="crm_prop_location_status_idx"), models.Index(fields=["listing_type", "property_type"], name="crm_prop_listing_type_idx")],
            },
        ),
        migrations.CreateModel(
            name="CallLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("direction", models.CharField(choices=[("inbound", "Incoming"), ("outbound", "Outgoing")], default="outbound", max_length=10)),
                ("outcome", models.CharField(choices=[("answered", "Answered"), ("no_answer", "No answer"), ("busy", "Busy"), ("voicemail", "Voicemail"), ("meeting", "Meeting booked"), ("not_interested", "Not interested")], default="answered", max_length=20)),
                ("duration_seconds", models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(86400)])),
                ("called_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("next_follow_up", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("agent", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="call_logs", to=settings.AUTH_USER_MODEL)),
                ("lead", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="call_logs", to="crm.lead")),
            ],
            options={"ordering": ["-called_at"], "indexes": [models.Index(fields=["agent", "called_at"], name="crm_call_agent_called_idx")]},
        ),
        migrations.CreateModel(
            name="Deal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(blank=True, max_length=180)),
                ("deal_type", models.CharField(choices=[("sale", "Sale"), ("rent", "Rental")], default="sale", max_length=10)),
                ("stage", models.CharField(choices=[("qualified", "Qualified"), ("viewing", "Viewing"), ("negotiation", "Negotiation"), ("won", "Won"), ("lost", "Lost")], db_index=True, default="qualified", max_length=15)),
                ("amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=15, validators=[django.core.validators.MinValueValidator(0)])),
                ("commission_rate", models.DecimalField(decimal_places=2, default=Decimal("2.00"), max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ("expected_close", models.DateField(blank=True, null=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_deals", to=settings.AUTH_USER_MODEL)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_deals", to=settings.AUTH_USER_MODEL)),
                ("lead", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="deals", to="crm.lead")),
                ("property", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="deals", to="crm.property")),
            ],
            options={"ordering": ["-updated_at"], "indexes": [models.Index(fields=["stage", "expected_close"], name="crm_deal_stage_close_idx"), models.Index(fields=["assigned_to", "stage"], name="crm_deal_assign_stage_idx")]},
        ),
        migrations.CreateModel(
            name="Task",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("todo", "To do"), ("in_progress", "In progress"), ("completed", "Completed"), ("cancelled", "Cancelled")], db_index=True, default="todo", max_length=15)),
                ("priority", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")], db_index=True, default="medium", max_length=10)),
                ("due_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_crm_tasks", to=settings.AUTH_USER_MODEL)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_crm_tasks", to=settings.AUTH_USER_MODEL)),
                ("lead", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tasks", to="crm.lead")),
                ("property", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tasks", to="crm.property")),
            ],
            options={"ordering": ["status", "due_at", "-created_at"], "indexes": [models.Index(fields=["assigned_to", "status", "due_at"], name="crm_task_assign_status_due_idx")]},
        ),
    ]
