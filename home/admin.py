from django.contrib import admin
from home.models import Home, FloorPlan


@admin.register(FloorPlan)
class FloorPlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'home']


class FloorPlanInline(admin.TabularInline):
    model = FloorPlan
    extra = 1


@admin.register(Home)
class HomeAdmin(admin.ModelAdmin):
    list_display = ['id', 'home_number']
    inlines = [FloorPlanInline]
