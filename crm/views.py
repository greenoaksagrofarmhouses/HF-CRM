import re
import csv
from calendar import month_abbr
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, ProtectedError, Q, Sum
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import CallLogForm, DealForm, LeadForm, PropertyForm, TaskForm
from .models import CallLog, ContactAccessLog, Deal, Lead, Property, Task
from .permissions import can_see_owner, is_manager, lead_visibility_q, visible_leads


def scope_leads(user):
    return visible_leads(user)


def scope_calls(user):
    qs = CallLog.objects.select_related("lead", "agent")
    if is_manager(user):
        return qs
    # Calls the agent logged stay in their history. Customer details on those rows
    # are masked by the template filters when the agent no longer has the lead.
    return qs.filter(Q(agent=user) | lead_visibility_q(user, "lead__"))


def scope_deals(user):
    qs = Deal.objects.select_related("lead", "property", "assigned_to", "created_by")
    return qs if is_manager(user) else qs.filter(Q(assigned_to=user) | Q(created_by=user))


def scope_tasks(user):
    qs = Task.objects.select_related("assigned_to", "lead", "property", "created_by")
    return qs if is_manager(user) else qs.filter(Q(assigned_to=user) | Q(created_by=user))


class UserFormKwargsMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class StampCreatorMixin:
    def form_valid(self, form):
        if hasattr(form.instance, "created_by") and not form.instance.pk:
            form.instance.created_by = self.request.user
        if hasattr(form.instance, "assigned_to") and not form.instance.assigned_to_id and not is_manager(self.request.user):
            form.instance.assigned_to = self.request.user
        if hasattr(form.instance, "assigned_agent") and not form.instance.assigned_agent_id and not is_manager(self.request.user):
            form.instance.assigned_agent = self.request.user
        if isinstance(form.instance, CallLog):
            form.instance.agent = self.request.user
        messages.success(self.request, self.success_message)
        response = super().form_valid(form)
        if isinstance(self.object, CallLog) and self.object.next_follow_up:
            lead = self.object.lead
            lead.next_follow_up = self.object.next_follow_up
            lead.save(update_fields=["next_follow_up", "updated_at"])
        return response


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "crm/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        month_start = today.replace(day=1)
        leads = scope_leads(self.request.user)
        calls = scope_calls(self.request.user)
        deals = scope_deals(self.request.user)
        tasks = scope_tasks(self.request.user)
        properties = Property.objects.all()
        context.update({
            "total_leads": leads.count(),
            "new_leads": leads.filter(status=Lead.Status.NEW).count(),
            "qualified_leads": leads.filter(status__in=[Lead.Status.QUALIFIED, Lead.Status.VIEWING, Lead.Status.NEGOTIATION]).count(),
            "won_leads": leads.filter(status=Lead.Status.WON).count(),
            "won_deals": deals.filter(stage=Deal.Stage.WON).count(),
            "properties_count": properties.count(),
            "available_properties": properties.filter(status=Property.Status.AVAILABLE).count(),
            "calls_today": calls.filter(called_at__date=today).count(),
            "calls_progress": min(calls.filter(called_at__date=today).count() * 8, 100),
            "open_tasks": tasks.exclude(status__in=[Task.Status.COMPLETED, Task.Status.CANCELLED]).count(),
            "overdue_tasks": tasks.filter(due_at__lt=timezone.now()).exclude(status__in=[Task.Status.COMPLETED, Task.Status.CANCELLED]).count(),
            "month_revenue": deals.filter(stage=Deal.Stage.WON, closed_at__date__gte=month_start, closed_at__date__lt=(month_start.replace(day=28) + timedelta(days=4)).replace(day=1)).aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
            "today": today,
            "open_pipeline": deals.exclude(stage__in=[Deal.Stage.WON, Deal.Stage.LOST]).aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
            "recent_leads": leads.order_by("-created_at")[:7],
            "upcoming_tasks": tasks.filter(due_at__gte=timezone.now()).exclude(status__in=[Task.Status.COMPLETED, Task.Status.CANCELLED]).order_by("due_at")[:6],
            "recent_calls": calls.order_by("-called_at")[:6],
            "pipeline_stages": [{"key": key, "label": label, "count": deals.filter(stage=key).count(), "amount": deals.filter(stage=key).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")} for key, label in Deal.Stage.choices],
        })
        # Month-by-month won revenue for the last six calendar months.
        chart_labels, chart_values = [], []
        for offset in range(5, -1, -1):
            month_index = today.month - offset
            year = today.year
            while month_index <= 0:
                month_index += 12
                year -= 1
            start = date(year, month_index, 1)
            end = date(year + (month_index == 12), 1 if month_index == 12 else month_index + 1, 1)
            total = deals.filter(stage=Deal.Stage.WON, closed_at__date__gte=start, closed_at__date__lt=end).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            chart_labels.append(f"{month_abbr[month_index]} {str(year)[-2:]}")
            chart_values.append(float(total))
        context["chart_labels"] = chart_labels
        context["chart_values"] = chart_values
        return context


class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = "crm/lead_list.html"
    context_object_name = "leads"
    paginate_by = 12

    def get_queryset(self):
        qs = scope_leads(self.request.user).order_by("-updated_at")
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "")
        priority = self.request.GET.get("priority", "")
        source = self.request.GET.get("source", "")
        if q:
            qs = qs.filter(Q(full_name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q) | Q(preferred_location__icontains=q))
        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=priority)
        if source:
            qs = qs.filter(source=source)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"query": self.request.GET.get("q", ""), "selected_status": self.request.GET.get("status", ""), "selected_priority": self.request.GET.get("priority", ""), "selected_source": self.request.GET.get("source", ""), "today": timezone.localdate(), "status_choices": Lead.Status.choices, "priority_choices": Lead.Priority.choices, "source_choices": Lead.Source.choices, "total_leads": scope_leads(self.request.user).count()})
        return context


class LeadCreateView(LoginRequiredMixin, UserFormKwargsMixin, StampCreatorMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = "crm/lead_form.html"
    success_message = "Lead created successfully."

    def get_success_url(self):
        return reverse("lead_detail", kwargs={"pk": self.object.pk})


class LeadUpdateView(LoginRequiredMixin, UserFormKwargsMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = "crm/lead_form.html"
    success_message = "Lead updated successfully."

    def get_queryset(self):
        return scope_leads(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("lead_detail", kwargs={"pk": self.object.pk})


class LeadDetailView(LoginRequiredMixin, DetailView):
    model = Lead
    template_name = "crm/lead_detail.html"
    context_object_name = "lead"

    def get_queryset(self):
        return scope_leads(self.request.user)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Logged only after the lookup succeeded, so 404s for other agents' leads leave no entry.
        ContactAccessLog.objects.create(actor=request.user, action=ContactAccessLog.Action.VIEWED_LEAD, lead_pk=self.object.pk)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["calls"] = self.object.call_logs.select_related("agent")[:8]
        context["tasks"] = scope_tasks(self.request.user).filter(lead=self.object).select_related("assigned_to").order_by("due_at")[:6]
        context["deals"] = scope_deals(self.request.user).filter(lead=self.object)
        context["today"] = timezone.localdate()
        return context


class CallListView(LoginRequiredMixin, ListView):
    model = CallLog
    template_name = "crm/call_list.html"
    context_object_name = "calls"
    paginate_by = 15

    def get_queryset(self):
        qs = scope_calls(self.request.user).order_by("-called_at")
        q = self.request.GET.get("q", "").strip()
        direction = self.request.GET.get("direction", "")
        if q:
            qs = qs.filter(Q(lead__full_name__icontains=q) | Q(lead__phone__icontains=q) | Q(notes__icontains=q))
        if direction:
            qs = qs.filter(direction=direction)
        return qs


class CallCreateView(LoginRequiredMixin, UserFormKwargsMixin, StampCreatorMixin, CreateView):
    model = CallLog
    form_class = CallLogForm
    template_name = "crm/call_form.html"
    success_message = "Call activity logged."

    def get_initial(self):
        initial = super().get_initial()
        lead_id = self.request.GET.get("lead")
        if lead_id:
            initial["lead"] = lead_id
        initial["called_at"] = timezone.localtime().strftime("%Y-%m-%dT%H:%M")
        return initial

    def get_success_url(self):
        return reverse("lead_detail", kwargs={"pk": self.object.lead_id})


class PropertyListView(LoginRequiredMixin, ListView):
    model = Property
    template_name = "crm/property_list.html"
    context_object_name = "properties"
    paginate_by = 12

    def get_queryset(self):
        qs = Property.objects.select_related("assigned_agent").all()
        q = self.request.GET.get("q", "").strip()
        listing_type = self.request.GET.get("listing_type", "")
        status = self.request.GET.get("status", "")
        property_type = self.request.GET.get("property_type", "")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(code__icontains=q) | Q(city__icontains=q) | Q(neighborhood__icontains=q))
        if listing_type:
            qs = qs.filter(listing_type=listing_type)
        if status:
            qs = qs.filter(status=status)
        if property_type:
            qs = qs.filter(property_type=property_type)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"query": self.request.GET.get("q", ""), "selected_listing_type": self.request.GET.get("listing_type", ""), "selected_status": self.request.GET.get("status", ""), "selected_property_type": self.request.GET.get("property_type", ""), "listing_choices": Property.ListingType.choices, "status_choices": Property.Status.choices, "type_choices": Property.PropertyType.choices})
        return context


class PropertyCreateView(LoginRequiredMixin, UserFormKwargsMixin, StampCreatorMixin, CreateView):
    model = Property
    form_class = PropertyForm
    template_name = "crm/property_form.html"
    success_message = "Property listing created."
    success_url = reverse_lazy("property_list")


class PropertyUpdateView(LoginRequiredMixin, UserFormKwargsMixin, UpdateView):
    model = Property
    form_class = PropertyForm
    template_name = "crm/property_form.html"
    success_url = reverse_lazy("property_list")

    def get_queryset(self):
        qs = Property.objects.all()
        if not is_manager(self.request.user):
            qs = qs.filter(Q(assigned_agent=self.request.user) | Q(created_by=self.request.user))
        return qs

    def form_valid(self, form):
        messages.success(self.request, "Property listing updated.")
        return super().form_valid(form)


class PropertyDetailView(LoginRequiredMixin, DetailView):
    model = Property
    template_name = "crm/property_detail.html"
    context_object_name = "property"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["deals"] = scope_deals(self.request.user).filter(property=self.object)
        context["tasks"] = scope_tasks(self.request.user).filter(property=self.object)[:5]
        context["can_see_owner"] = can_see_owner(self.request.user, self.object)
        return context


class DealListView(LoginRequiredMixin, ListView):
    model = Deal
    template_name = "crm/deal_list.html"
    context_object_name = "deals"
    paginate_by = 12

    def get_queryset(self):
        qs = scope_deals(self.request.user).order_by("-updated_at")
        q = self.request.GET.get("q", "").strip()
        stage = self.request.GET.get("stage", "")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(lead__full_name__icontains=q) | Q(property__title__icontains=q))
        if stage:
            qs = qs.filter(stage=stage)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"query": self.request.GET.get("q", ""), "selected_stage": self.request.GET.get("stage", ""), "stage_choices": Deal.Stage.choices, "open_value": self.get_queryset().exclude(stage__in=[Deal.Stage.WON, Deal.Stage.LOST]).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")})
        return context


class DealCreateView(LoginRequiredMixin, UserFormKwargsMixin, StampCreatorMixin, CreateView):
    model = Deal
    form_class = DealForm
    template_name = "crm/deal_form.html"
    success_message = "Deal added to pipeline."
    success_url = reverse_lazy("deal_list")


class DealUpdateView(LoginRequiredMixin, UserFormKwargsMixin, UpdateView):
    model = Deal
    form_class = DealForm
    template_name = "crm/deal_form.html"
    success_url = reverse_lazy("deal_list")

    def get_queryset(self):
        return scope_deals(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Deal updated successfully.")
        return super().form_valid(form)


class DealDetailView(LoginRequiredMixin, DetailView):
    model = Deal
    template_name = "crm/deal_detail.html"
    context_object_name = "deal"

    def get_queryset(self):
        return scope_deals(self.request.user)


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "crm/task_list.html"
    context_object_name = "tasks"
    paginate_by = 15

    def get_queryset(self):
        qs = scope_tasks(self.request.user).order_by("status", "due_at", "-created_at")
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(lead__full_name__icontains=q))
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"query": self.request.GET.get("q", ""), "selected_status": self.request.GET.get("status", ""), "status_choices": Task.Status.choices})
        return context


class TaskCreateView(LoginRequiredMixin, UserFormKwargsMixin, StampCreatorMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "crm/task_form.html"
    success_message = "Task created successfully."
    success_url = reverse_lazy("task_list")


class TaskUpdateView(LoginRequiredMixin, UserFormKwargsMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "crm/task_form.html"
    success_url = reverse_lazy("task_list")

    def get_queryset(self):
        return scope_tasks(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Task updated successfully.")
        return super().form_valid(form)


class TaskCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(scope_tasks(request.user), pk=pk)
        task.status = Task.Status.COMPLETED if task.status != Task.Status.COMPLETED else Task.Status.TODO
        task.save(update_fields=["status", "completed_at", "updated_at"])
        messages.success(request, "Task marked completed." if task.status == Task.Status.COMPLETED else "Task moved back to To do.")
        next_url = request.POST.get("next", "")
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return redirect(next_url)
        return redirect("task_list")


class DeleteObjectView(LoginRequiredMixin, DeleteView):
    template_name = "crm/delete_confirm.html"
    failure_url_name = None

    def get_success_url(self):
        return reverse(self.success_url_name)

    def form_valid(self, form):
        label = str(self.object)
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                f"{label} cannot be deleted while other records depend on it. Close or reassign those records first.",
            )
            if self.failure_url_name:
                return redirect(self.failure_url_name, pk=self.object.pk)
            return redirect(self.success_url_name)
        messages.success(self.request, f"{label} deleted.")
        return response


class LeadDeleteView(DeleteObjectView):
    model = Lead
    success_url_name = "lead_list"
    failure_url_name = "lead_detail"
    def get_queryset(self): return scope_leads(self.request.user)


class PropertyDeleteView(DeleteObjectView):
    model = Property
    success_url_name = "property_list"
    failure_url_name = "property_detail"
    def get_queryset(self):
        qs = Property.objects.all()
        if not is_manager(self.request.user):
            qs = qs.filter(Q(assigned_agent=self.request.user) | Q(created_by=self.request.user))
        return qs


class DealDeleteView(DeleteObjectView):
    model = Deal
    success_url_name = "deal_list"
    failure_url_name = "deal_detail"
    def get_queryset(self): return scope_deals(self.request.user)


class TaskDeleteView(DeleteObjectView):
    model = Task
    success_url_name = "task_list"
    def get_queryset(self): return scope_tasks(self.request.user)


class LeadExportView(LoginRequiredMixin, View):
    def get(self, request):
        if not is_manager(request.user):
            return HttpResponseForbidden("Only managers can export the full lead list.")
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="hartus-leads.csv"'
        response.write("\ufeff")  # Excel-friendly UTF-8 BOM.
        writer = csv.writer(response)
        writer.writerow(["Name", "Phone", "Email", "Source", "Status", "Interest", "Property type", "Area", "Budget min", "Budget max", "Location", "Priority", "Assigned to", "Next follow-up", "Created"])
        def phone_cell(value):
            # Excel drops leading zeros from numbers. Writing digits-only phone
            # numbers as ="0300..." keeps them as text. Anything else is left alone
            # so it cannot become a formula.
            value = "" if value is None else str(value).strip()
            if re.fullmatch(r"[0-9+()\- ]{3,32}", value):
                return '="' + value + '"'
            return safe_cell(value)

        def safe_cell(value):
            value = "" if value is None else str(value)
            # Avoid spreadsheet formula execution if user-controlled text is opened in Excel.
            if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
                return "'" + value
            return value
        export_qs = scope_leads(request.user).order_by("-created_at")
        ContactAccessLog.objects.create(actor=request.user, action=ContactAccessLog.Action.EXPORTED_LEADS, row_count=export_qs.count())
        for lead in export_qs:
            row = [lead.full_name, phone_cell(lead.phone), lead.email, lead.get_source_display(), lead.get_status_display(), lead.get_interest_display(), lead.property_type, (format(lead.desired_area.normalize(), "f") + " " + lead.get_desired_area_unit_display() if lead.desired_area else ""), lead.budget_min or "", lead.budget_max or "", lead.preferred_location, lead.get_priority_display(), (lead.assigned_to.get_full_name() or lead.assigned_to.username) if lead.assigned_to else "", lead.next_follow_up.strftime("%d-%m-%y") if lead.next_follow_up else "", timezone.localtime(lead.created_at).strftime("%d-%m-%y")]
            writer.writerow([value if i == 1 else safe_cell(value) for i, value in enumerate(row)])
        return response


class GlobalSearchView(LoginRequiredMixin, TemplateView):
    template_name = "crm/global_search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "").strip()
        context["query"] = q
        context["leads"] = scope_leads(self.request.user).filter(Q(full_name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q))[:8] if q else []
        context["properties"] = Property.objects.filter(Q(title__icontains=q) | Q(code__icontains=q) | Q(neighborhood__icontains=q))[:8] if q else []
        context["deals"] = scope_deals(self.request.user).filter(Q(title__icontains=q) | Q(lead__full_name__icontains=q))[:8] if q else []
        context["tasks"] = scope_tasks(self.request.user).filter(title__icontains=q)[:8] if q else []
        return context
