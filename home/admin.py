from django.contrib import admin
from home.models import Home


@admin.register(Home)
class HomeAdmin(admin.ModelAdmin):
    list_display = ['id', 'home_number']
