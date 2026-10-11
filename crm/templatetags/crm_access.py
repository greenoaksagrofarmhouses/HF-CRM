from django import template

from crm.permissions import can_view_lead as _can_view_lead

register = template.Library()


@register.filter
def can_view_lead(lead, user):
    return _can_view_lead(user, lead)


@register.filter
def lead_name(lead, user):
    return lead.full_name if _can_view_lead(user, lead) else "Restricted client"


@register.filter
def lead_phone(lead, user):
    return lead.phone if _can_view_lead(user, lead) else ""


@register.filter
def lead_initials(lead, user):
    return lead.initials if _can_view_lead(user, lead) else "•"


@register.filter
def deal_title(deal, user):
    return deal.title if _can_view_lead(user, deal.lead) else f"Restricted deal #{deal.pk}"
