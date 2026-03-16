from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .forms import UserAdminCreateForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserAdminCreateForm
    model = User

    list_display = ("id", "username", "role", "is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Info", {"fields": ("full_name", "phone_number", "role")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "is_active")}),
    )

    add_fieldsets = ((None, {
        "classes": ("wide",),
        "fields": ("username", "password")})
    )
