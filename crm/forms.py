from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import CallLog, Deal, Lead, Property, Task
from .permissions import is_manager, lead_choices

User = get_user_model()

BASE_INPUT = "field-control"

# Preset plot sizes staff can pick. Value format is "unit:size".
AREA_OPTIONS = [("", "Not decided yet")]
AREA_OPTIONS += [(f"marla:{v}", f"{v} Marla") for v in (3, 5, 7, 10, 12, 15, 20, 25, 30)]
AREA_OPTIONS += [(f"kanal:{v}", f"{v} Kanal") for v in (1, 2, 3, 4, 5, 10)]


class StyledModelForm(forms.ModelForm):
    """Applies a consistent, accessible input class to all Django form widgets."""
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "field-checkbox")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", BASE_INPUT + " select-control")
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", BASE_INPUT + " field-textarea")
                widget.attrs.setdefault("rows", 4)
            else:
                widget.attrs.setdefault("class", BASE_INPUT)
            widget.attrs.setdefault("placeholder", field.help_text or field.label or name.replace("_", " ").title())


def visible_users_for(user):
    qs = User.objects.filter(is_active=True).order_by("first_name", "username")
    if user and user.is_authenticated and not (user.is_staff or user.is_superuser):
        qs = qs.filter(pk=user.pk)
    return qs


class LeadForm(StyledModelForm):
    area_option = forms.ChoiceField(choices=AREA_OPTIONS, required=False, label="Plot size needed")

    class Meta:
        model = Lead
        exclude = ["created_at", "updated_at", "created_by"]
        widgets = {
            "next_follow_up": forms.DateInput(attrs={"type": "date"}),
            "budget_min": forms.NumberInput(attrs={"step": "1000", "min": "0"}),
            "budget_max": forms.NumberInput(attrs={"step": "1000", "min": "0"}),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = visible_users_for(self.user)
        if self.user and self.user.is_authenticated and not (self.user.is_staff or self.user.is_superuser):
            self.fields["assigned_to"].initial = self.user
        if not is_manager(self.user):
            # Agents cannot leave a lead unassigned, which would hand it to nobody.
            self.fields["assigned_to"].required = True
        # Staff pick one preset size; the free-text size fields are not shown.
        self.fields.pop("desired_area", None)
        self.fields.pop("desired_area_unit", None)
        self.order_fields(["property_type", "area_option", "budget_min", "budget_max", "preferred_location"])
        inst = self.instance
        if inst.pk and inst.desired_area and inst.desired_area_unit:
            self.initial["area_option"] = f"{inst.desired_area_unit}:{int(inst.desired_area)}"

    def clean(self):
        cleaned = super().clean()
        minimum, maximum = cleaned.get("budget_min"), cleaned.get("budget_max")
        if minimum is not None and maximum is not None and minimum > maximum:
            self.add_error("budget_max", "Maximum budget must be greater than or equal to minimum budget.")
        option = cleaned.get("area_option", "")
        if option:
            unit, _, size = option.partition(":")
            self.instance.desired_area = Decimal(size)
            self.instance.desired_area_unit = unit
        else:
            self.instance.desired_area = None
            self.instance.desired_area_unit = ""
        return cleaned


class CallLogForm(StyledModelForm):
    class Meta:
        model = CallLog
        exclude = ["created_at", "updated_at", "agent"]
        widgets = {
            "called_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "next_follow_up": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lead"].queryset = lead_choices(self.user, self.instance.lead_id if self.instance.pk else None)
        self.fields["lead"].empty_label = "Select a lead"
        if self.user and self.user.is_authenticated:
            self.fields["called_at"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"]


class PropertyForm(StyledModelForm):
    class Meta:
        model = Property
        exclude = ["created_at", "updated_at", "created_by", "code"]
        widgets = {"description": forms.Textarea(attrs={"rows": 5}), "price": forms.NumberInput(attrs={"min": "0", "step": "1000"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_agent"].queryset = visible_users_for(self.user)


class DealForm(StyledModelForm):
    class Meta:
        model = Deal
        exclude = ["created_at", "updated_at", "created_by", "closed_at"]
        widgets = {"expected_close": forms.DateInput(attrs={"type": "date"}), "amount": forms.NumberInput(attrs={"min": "0", "step": "1000"}), "commission_rate": forms.NumberInput(attrs={"min": "0", "max": "100", "step": "0.25"}), "notes": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lead"].queryset = lead_choices(self.user, self.instance.lead_id if self.instance.pk else None)
        self.fields["property"].queryset = Property.objects.order_by("title")
        self.fields["assigned_to"].queryset = visible_users_for(self.user)
        self.fields["property"].required = False
        if self.user and self.user.is_authenticated and not (self.user.is_staff or self.user.is_superuser):
            self.fields["assigned_to"].initial = self.user


class TaskForm(StyledModelForm):
    class Meta:
        model = Task
        exclude = ["created_at", "updated_at", "created_by", "completed_at"]
        widgets = {"due_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"), "description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = visible_users_for(self.user)
        self.fields["lead"].queryset = lead_choices(self.user, self.instance.lead_id if self.instance.pk else None)
        self.fields["property"].queryset = Property.objects.order_by("title")
        self.fields["lead"].required = False
        self.fields["property"].required = False
        if "due_at" in self.fields:
            self.fields["due_at"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]
        if self.user and self.user.is_authenticated and not (self.user.is_staff or self.user.is_superuser):
            self.fields["assigned_to"].initial = self.user
