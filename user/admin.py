from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
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
        }))
