import builtins
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Lead(TimeStampedModel):
    class Source(models.TextChoices):
        WEBSITE = "website", "Website"
        WHATSAPP = "whatsapp", "WhatsApp"
        FACEBOOK = "facebook", "Facebook / Instagram"
        PORTAL = "portal", "Property portal"
        REFERRAL = "referral", "Referral"
        WALK_IN = "walk_in", "Walk-in"
        COLD_CALL = "cold_call", "Cold call"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUALIFIED = "qualified", "Qualified"
        VIEWING = "viewing", "Viewing scheduled"
        NEGOTIATION = "negotiation", "Negotiation"
        WON = "won", "Won"
        LOST = "lost", "Lost"

    class Interest(models.TextChoices):
        BUY = "buy", "Buying"
        RENT = "rent", "Renting"
        SELL = "sell", "Selling"
        INVEST = "invest", "Investment"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    full_name = models.CharField(max_length=160, db_index=True)
    company = models.CharField(max_length=160, blank=True)
    phone = models.CharField(max_length=32, db_index=True)
    email = models.EmailField(blank=True)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.OTHER, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)
    interest = models.CharField(max_length=12, choices=Interest.choices, default=Interest.BUY)
    property_type = models.CharField(max_length=40, blank=True, help_text="Apartment, house, plot, commercial, etc.")
    desired_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Desired area")
    desired_area_unit = models.CharField(max_length=12, choices=[("sqft", "Sq ft"), ("sqyd", "Sq yd"), ("marla", "Marla"), ("kanal", "Kanal")], blank=True, default="", verbose_name="Area unit")
    budget_min = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    budget_max = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    preferred_location = models.CharField(max_length=180, blank=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM, db_index=True)
    next_follow_up = models.DateField(null=True, blank=True, db_index=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_leads")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_leads")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        indexes = [models.Index(fields=["status", "priority"], name="crm_lead_status_prio_idx"), models.Index(fields=["assigned_to", "next_follow_up"], name="crm_lead_assign_follow_idx")]

    def __str__(self):
        return f"{self.full_name} · {self.phone}"

    @property
    def initials(self):
        return "".join(part[0] for part in self.full_name.split()[:2]).upper() or "L"

    @property
    def budget_label(self):
        if self.budget_min and self.budget_max:
            return f"PKR {self.budget_min:,.0f}–{self.budget_max:,.0f}"
        if self.budget_max:
            return f"Up to PKR {self.budget_max:,.0f}"
        if self.budget_min:
            return f"From PKR {self.budget_min:,.0f}"
        return "Not specified"


class Property(TimeStampedModel):
    class ListingType(models.TextChoices):
        SALE = "sale", "For sale"
        RENT = "rent", "For rent"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        SOLD = "sold", "Sold"
        RENTED = "rented", "Rented"
        OFF_MARKET = "off_market", "Off market"

    class PropertyType(models.TextChoices):
        HOUSE = "house", "House"
        APARTMENT = "apartment", "Apartment"
        PLOT = "plot", "Plot"
        COMMERCIAL = "commercial", "Commercial"
        OFFICE = "office", "Office"
        FARMHOUSE = "farmhouse", "Farmhouse"
        OTHER = "other", "Other"

    title = models.CharField(max_length=180, db_index=True)
    code = models.CharField(max_length=24, unique=True, blank=True, help_text="Leave blank to generate a reference code.")
    property_type = models.CharField(max_length=20, choices=PropertyType.choices, default=PropertyType.HOUSE)
    listing_type = models.CharField(max_length=10, choices=ListingType.choices, default=ListingType.SALE)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.AVAILABLE, db_index=True)
    price = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    bedrooms = models.PositiveSmallIntegerField(default=0)
    bathrooms = models.PositiveSmallIntegerField(default=0)
    area_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    area_unit = models.CharField(max_length=12, choices=[("sqft", "sq ft"), ("sqyd", "sq yd"), ("marla", "marla"), ("kanal", "kanal")], default="marla")
    city = models.CharField(max_length=80, default="Lahore", db_index=True)
    neighborhood = models.CharField(max_length=140, blank=True, db_index=True)
    address = models.CharField(max_length=240, blank=True)
    owner_name = models.CharField(max_length=160, blank=True)
    owner_phone = models.CharField(max_length=32, blank=True)
    description = models.TextField(blank=True)
    featured = models.BooleanField(default=False)
    assigned_agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_properties")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_properties")

    class Meta:
        ordering = ["-featured", "-created_at"]
        indexes = [models.Index(fields=["city", "neighborhood", "status"], name="crm_prop_location_status_idx"), models.Index(fields=["listing_type", "property_type"], name="crm_prop_listing_type_idx")]

    def save(self, *args, **kwargs):
        if not self.code:
            # Retry-safe enough for ordinary local use; uniqueness remains enforced by the database.
            import uuid
            self.code = f"NX-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.code})"

    @property
    def location_label(self):
        return ", ".join(part for part in [self.neighborhood, self.city] if part)


class CallLog(TimeStampedModel):
    class Direction(models.TextChoices):
        INBOUND = "inbound", "Incoming"
        OUTBOUND = "outbound", "Outgoing"

    class Outcome(models.TextChoices):
        ANSWERED = "answered", "Answered"
        NO_ANSWER = "no_answer", "No answer"
        BUSY = "busy", "Busy"
        VOICEMAIL = "voicemail", "Voicemail"
        MEETING = "meeting", "Meeting booked"
        NOT_INTERESTED = "not_interested", "Not interested"

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="call_logs")
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="call_logs")
    direction = models.CharField(max_length=10, choices=Direction.choices, default=Direction.OUTBOUND)
    outcome = models.CharField(max_length=20, choices=Outcome.choices, default=Outcome.ANSWERED)
    duration_seconds = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(86400)])
    called_at = models.DateTimeField(default=timezone.now, db_index=True)
    next_follow_up = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-called_at"]
        indexes = [models.Index(fields=["agent", "called_at"], name="crm_call_agent_called_idx")]

    def __str__(self):
        return f"{self.get_direction_display()} call · {self.lead.full_name} · {self.called_at:%Y-%m-%d %H:%M}"

    @property
    def duration_label(self):
        minutes, seconds = divmod(self.duration_seconds, 60)
        return f"{minutes}:{seconds:02d}" if minutes else f"{seconds}s"


class Deal(TimeStampedModel):
    class Type(models.TextChoices):
        SALE = "sale", "Sale"
        RENT = "rent", "Rental"

    class Stage(models.TextChoices):
        QUALIFIED = "qualified", "Qualified"
        VIEWING = "viewing", "Viewing"
        NEGOTIATION = "negotiation", "Negotiation"
        WON = "won", "Won"
        LOST = "lost", "Lost"

    lead = models.ForeignKey(Lead, on_delete=models.PROTECT, related_name="deals")
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, related_name="deals")
    title = models.CharField(max_length=180, blank=True)
    deal_type = models.CharField(max_length=10, choices=Type.choices, default=Type.SALE)
    stage = models.CharField(max_length=15, choices=Stage.choices, default=Stage.QUALIFIED, db_index=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(0)])
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("2.00"), validators=[MinValueValidator(0), MaxValueValidator(100)])
    expected_close = models.DateField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_deals")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_deals")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["stage", "expected_close"], name="crm_deal_stage_close_idx"), models.Index(fields=["assigned_to", "stage"], name="crm_deal_assign_stage_idx")]

    def save(self, *args, **kwargs):
        if not self.title and self.lead_id:
            self.title = f"{self.lead.full_name} · {self.get_deal_type_display()}"
        if self.stage == self.Stage.WON and self.closed_at is None:
            self.closed_at = timezone.now()
        elif self.stage != self.Stage.WON:
            self.closed_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"Deal #{self.pk}"

    @builtins.property
    def commission_amount(self):
        return (self.amount * self.commission_rate / Decimal("100")).quantize(Decimal("0.01"))


class Task(TimeStampedModel):
    class Status(models.TextChoices):
        TODO = "todo", "To do"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.TODO, db_index=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM, db_index=True)
    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_crm_tasks")
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_crm_tasks")

    class Meta:
        ordering = ["status", "due_at", "-created_at"]
        indexes = [models.Index(fields=["assigned_to", "status", "due_at"], name="crm_task_assign_status_due_idx")]

    def save(self, *args, **kwargs):
        if self.status == self.Status.COMPLETED and self.completed_at is None:
            self.completed_at = timezone.now()
        elif self.status != self.Status.COMPLETED:
            self.completed_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @builtins.property
    def is_overdue(self):
        return bool(self.due_at and self.status not in [self.Status.COMPLETED, self.Status.CANCELLED] and self.due_at < timezone.now())


class ContactAccessLog(models.Model):
    """Audit trail for who viewed customer records and who exported them.

    Rows are never edited or deleted from the app. The lead is stored as a plain
    number so the trail survives if the lead is deleted later.
    """
    class Action(models.TextChoices):
        VIEWED_LEAD = "viewed_lead", "Viewed lead"
        EXPORTED_LEADS = "exported_leads", "Exported leads"

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="contact_access_logs")
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    lead_pk = models.PositiveBigIntegerField(null=True, blank=True, db_index=True)
    row_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact access log"
        verbose_name_plural = "Contact access logs"

    def __str__(self):
        return f"{self.get_action_display()} by {self.actor} at {self.created_at:%Y-%m-%d %H:%M}"
