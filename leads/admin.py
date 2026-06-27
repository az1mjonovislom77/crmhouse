from django.contrib import admin
from leads.models import Lead, LeadEvent


class LeadEventInline(admin.TabularInline):
    model  = LeadEvent
    extra  = 0
    fields = ['type', 'from_value', 'to_value', 'text', 'meeting_at', 'meeting_type', 'by', 'at']
    readonly_fields = ['at']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display  = ['id', 'full_name', 'phone', 'board', 'status', 'sub_status', 'owner', 'score', 'created_at']
    list_filter   = ['board', 'status', 'source']
    search_fields = ['full_name', 'phone', 'email']
    inlines       = [LeadEventInline]


@admin.register(LeadEvent)
class LeadEventAdmin(admin.ModelAdmin):
    list_display  = ['id', 'lead', 'type', 'from_value', 'to_value', 'by', 'at']
    list_filter   = ['type']
    search_fields = ['lead__full_name', 'text']
