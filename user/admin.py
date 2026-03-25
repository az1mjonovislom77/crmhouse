from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "role", "is_staff", "is_active")
    search_fields = ("username", "full_name", "phone_number")
    ordering = ("-id",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Info", {"fields": ("full_name", "phone_number", "role")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "is_active")}),
    )

    def save_model(self, request, obj, form, change):
        if obj.password and not obj.password.startswith("pbkdf2_"):
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)
