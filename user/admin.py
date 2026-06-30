from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, RequestLog
from .forms import UserAdminCreateForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserAdminCreateForm

    list_display = ("id", "username", "role", "is_staff", "is_active")
    search_fields = ("username", "full_name", "phone_number")
    ordering = ("-id",)
    list_filter = ("role", "is_staff", "is_active")

    readonly_fields = ("id",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Info", {"fields": ("full_name", "phone_number", "role")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "is_active")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password"),
        }),
    )


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "method", "path", "status_code", "duration_ms", "ip_address", "created_at")
    list_filter = ("method", "status_code")
    search_fields = ("path", "user__username", "user__full_name", "ip_address")
    readonly_fields = ("user", "method", "path", "status_code", "duration_ms", "ip_address", "created_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
