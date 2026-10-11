from django.contrib import admin
from .models import CallLog, ContactAccessLog, Deal, Lead, Property, Task


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "status", "source", "priority", "assigned_to", "next_follow_up", "updated_at")
    list_filter = ("status", "source", "priority", "interest", "created_at")
    search_fields = ("full_name", "phone", "email", "preferred_location")
    autocomplete_fields = ("assigned_to", "created_by")
    date_hierarchy = "created_at"


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "property_type", "listing_type", "price", "city", "status", "featured")
    list_filter = ("status", "listing_type", "property_type", "city", "featured")
    search_fields = ("code", "title", "neighborhood", "city", "owner_name", "owner_phone")
    autocomplete_fields = ("assigned_agent", "created_by")


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ("lead", "agent", "direction", "outcome", "called_at", "duration_seconds")
    list_filter = ("direction", "outcome", "called_at")
    search_fields = ("lead__full_name", "lead__phone", "notes")
    autocomplete_fields = ("lead", "agent")


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ("title", "lead", "property", "stage", "amount", "commission_rate", "expected_close", "assigned_to")
    list_filter = ("stage", "deal_type", "created_at")
    search_fields = ("title", "lead__full_name", "property__title")
    autocomplete_fields = ("lead", "property", "assigned_to", "created_by")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "priority", "assigned_to", "due_at", "lead", "property")
    list_filter = ("status", "priority", "due_at")
    search_fields = ("title", "description", "lead__full_name", "property__title")
    autocomplete_fields = ("assigned_to", "lead", "property", "created_by")


@admin.register(ContactAccessLog)
class ContactAccessLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "lead_pk", "row_count")
    list_filter = ("action", "created_at")
    search_fields = ("actor__username", "lead_pk")
    readonly_fields = ("actor", "action", "lead_pk", "row_count", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
