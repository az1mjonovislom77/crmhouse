from django.contrib import admin
from contact_center.models import CallRecord


@admin.register(CallRecord)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'clid', 'src', 'dst', 'disposition', 'duration', 'calldate', 'created_at')
    list_filter = ('disposition',)
    search_fields = ('clid', 'src', 'dst', 'uniqueid')
    ordering = ('-calldate',)
