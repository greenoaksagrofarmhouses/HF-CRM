from datetime import timedelta
from decimal import Decimal
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from crm.models import CallLog, Deal, Lead, Property, Task

User = get_user_model()


class Command(BaseCommand):
    help = "Create clearly synthetic sample CRM records for a demo workspace."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="", help="Existing user to own the demo records. Defaults to the first staff user.")
        parser.add_argument("--count", type=int, default=18, help="Number of leads to create (default: 18).")
        parser.add_argument("--clear-demo", action="store_true", help="Delete records whose names/titles start with DEMO before seeding.")

    def handle(self, *args, **options):
        count = max(1, min(options["count"], 100))
        user = User.objects.filter(username=options["username"]).first() if options["username"] else User.objects.filter(is_staff=True).order_by("id").first()
        if not user:
            raise CommandError("Create a staff user first with `python manage.py createsuperuser`, then rerun seed_demo.")
        if options["clear_demo"]:
            Task.objects.filter(title__startswith="DEMO ").delete()
            CallLog.objects.filter(notes__startswith="DEMO ").delete()
            Deal.objects.filter(title__startswith="DEMO ").delete()
            Lead.objects.filter(full_name__startswith="DEMO ").delete()
            Property.objects.filter(title__startswith="DEMO ").delete()
        rng = random.Random(42)
        locations = ["DHA Phase 6, Lahore", "Gulberg, Lahore", "Bahria Town, Lahore", "Lake City, Lahore", "Askari 10, Lahore", "Model Town, Lahore", "Johar Town, Lahore"]
        names = ["Ayesha Khan", "Hamza Malik", "Sara Ahmed", "Ali Raza", "Mariam Shah", "Usman Tariq", "Zara Iqbal", "Bilal Hussain", "Hira Siddiqui", "Omar Farooq", "Amna Javed", "Daniyal Sheikh", "Noor Fatima", "Saad Qureshi", "Mahnoor Ali", "Rayan Shah", "Inaya Mahmood", "Ahmed Zafar", "Eman Khalid", "Fahad Mir"]
        property_types = [Property.PropertyType.HOUSE, Property.PropertyType.APARTMENT, Property.PropertyType.PLOT, Property.PropertyType.COMMERCIAL, Property.PropertyType.FARMHOUSE]
        properties = []
        for i in range(7):
            ptype = property_types[i % len(property_types)]
            listing = Property.ListingType.RENT if i in (1, 4) else Property.ListingType.SALE
            price = Decimal(rng.choice(["8500000", "12500000", "18500000", "24500000", "39000000", "55000000", "82500000"]))
            prop = Property.objects.create(
                title=f"DEMO {['Garden Residence', 'Parkview Apartment', 'Corner Plot', 'Signature Office', 'Canal Farmhouse', 'Modern Family Home', 'Executive Suite'][i]}",
                property_type=ptype, listing_type=listing, status=Property.Status.AVAILABLE,
                price=price, bedrooms=0 if ptype in [Property.PropertyType.PLOT, Property.PropertyType.COMMERCIAL] else rng.choice([2, 3, 4, 5]),
                bathrooms=rng.choice([2, 3, 4]), area_value=Decimal(rng.choice(["5", "7", "10", "12", "20"])),
                area_unit=rng.choice(["marla", "kanal"]), city="Lahore", neighborhood=rng.choice(locations).split(",")[0],
                address="Synthetic demo listing — replace with verified listing details.", owner_name=f"Demo Owner {i+1}", owner_phone="0300-0000000",
                description="Sample record created by the seed_demo command. Replace with verified property information before real use.",
                featured=i < 2, assigned_agent=user, created_by=user,
            )
            properties.append(prop)
        lead_objects = []
        today = timezone.localdate()
        for i in range(count):
            name = names[i % len(names)]
            budget_pair = rng.choice([("5000000", "15000000"), ("8000000", "25000000"), ("12000000", "40000000"), ("20000000", "90000000")])
            lead = Lead.objects.create(
                full_name=f"DEMO {name}", phone=f"0300-{1000000+i:07d}", email=f"demo.lead{i+1}@example.invalid",
                source=list(Lead.Source.values())[i % len(Lead.Source.values())],
                status=[Lead.Status.NEW, Lead.Status.CONTACTED, Lead.Status.QUALIFIED, Lead.Status.VIEWING, Lead.Status.NEGOTIATION, Lead.Status.WON][i % 6],
                interest=list(Lead.Interest.values())[i % len(Lead.Interest.values())],
                property_type=properties[i % len(properties)].get_property_type_display(),
                budget_min=Decimal(budget_pair[0]),
                budget_max=Decimal(budget_pair[1]),
                preferred_location=locations[i % len(locations)], priority=[Lead.Priority.MEDIUM, Lead.Priority.HIGH, Lead.Priority.LOW, Lead.Priority.URGENT][i % 4],
                next_follow_up=today + timedelta(days=(i % 9) - 2), assigned_to=user, created_by=user,
                notes="DEMO record. Replace this note with verified client requirements and consent-aware contact notes.",
            )
            lead_objects.append(lead)
            CallLog.objects.create(lead=lead, agent=user, direction=CallLog.Direction.OUTBOUND if i % 2 else CallLog.Direction.INBOUND,
                outcome=list(CallLog.Outcome.values())[i % len(CallLog.Outcome.values())], duration_seconds=rng.choice([72, 125, 240, 315]),
                called_at=timezone.now() - timedelta(days=i % 10, hours=i % 6), next_follow_up=lead.next_follow_up,
                notes="DEMO call record: replace with the actual call outcome.")
            if i < len(properties):
                stage = [Deal.Stage.QUALIFIED, Deal.Stage.VIEWING, Deal.Stage.NEGOTIATION, Deal.Stage.WON, Deal.Stage.LOST][i % 5]
                Deal.objects.create(lead=lead, property=properties[i % len(properties)], title=f"DEMO Opportunity {i+1:02d} · {name}",
                    deal_type=Deal.Type.RENT if i % 4 == 0 else Deal.Type.SALE, stage=stage,
                    amount=properties[i % len(properties)].price, commission_rate=Decimal("2.00"),
                    expected_close=today + timedelta(days=5 + i * 2), assigned_to=user, created_by=user,
                    notes="DEMO opportunity. Confirm commercial terms before using this record operationally.")
            Task.objects.create(title=f"DEMO Follow up with {name}", description="Sample task: verify the contact's preferred time before reaching out.",
                status=Task.Status.COMPLETED if i % 5 == 0 else Task.Status.TODO,
                priority=[Task.Priority.MEDIUM, Task.Priority.HIGH, Task.Priority.LOW][i % 3],
                due_at=timezone.now() + timedelta(days=(i % 7) - 2, hours=i % 8), assigned_to=user, lead=lead, created_by=user)
        self.stdout.write(self.style.SUCCESS(f"Created demo records for {user.username}: {len(lead_objects)} leads, {len(properties)} properties, {CallLog.objects.filter(agent=user, notes__startswith='DEMO ').count()} calls, and sample deals/tasks."))
        self.stdout.write(self.style.WARNING("All seeded names, phone numbers, listings and activity are synthetic. Do not use them as real customer data."))
