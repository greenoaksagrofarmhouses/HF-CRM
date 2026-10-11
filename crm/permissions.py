"""Central access rules for Hartus Floare CRM.

Every list, detail, form dropdown, export and search must use these helpers so
the rules cannot drift apart.

Rules
-----
* Managers (staff or superuser) can see everything.
* An agent can see a lead when it is assigned to them, or when it is unassigned
  and they created it. Reassigning a lead removes the previous agent's access.
* Property owner name and phone are visible only to managers, the assigned
  agent and the creator. Other listing details are shared across agents.
* Deals, tasks and calls stay scoped to their own assignee, creator or agent.
  Any customer name, phone or email shown next to them follows the lead rule.
"""
from django.db.models import Q

from .models import Lead


def is_manager(user):
    return bool(user is not None and user.is_authenticated and (user.is_staff or user.is_superuser))


def lead_visibility_q(user, prefix=""):
    """Q matching leads the user may see. Use prefix="lead__" when starting from another model."""
    return (
        Q(**{f"{prefix}assigned_to": user})
        | Q(**{f"{prefix}assigned_to__isnull": True, f"{prefix}created_by": user})
    )


def can_view_lead(user, lead):
    if lead is None or user is None or not user.is_authenticated:
        return False
    if is_manager(user):
        return True
    if lead.assigned_to_id is None:
        return lead.created_by_id == user.pk
    return lead.assigned_to_id == user.pk


def visible_leads(user):
    qs = Lead.objects.select_related("assigned_to", "created_by")
    if is_manager(user):
        return qs
    return qs.filter(lead_visibility_q(user))


def lead_choices(user, current_lead_id=None):
    """Leads a form may offer. The record's current lead stays selectable so existing records remain editable."""
    qs = visible_leads(user)
    if current_lead_id:
        qs = Lead.objects.filter(Q(pk__in=qs.values("pk")) | Q(pk=current_lead_id))
    return qs.order_by("full_name")


def can_see_owner(user, prop):
    if is_manager(user):
        return True
    return user.is_authenticated and user.pk in {prop.assigned_agent_id, prop.created_by_id}
