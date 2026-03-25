from django.contrib import admin
from home.models import Home, FloorPlan


@admin.register(FloorPlan)
class FloorPlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'home']


@admin.register(Home)
class HomeAdmin(admin.ModelAdmin):
    list_display = ['id', 'home_number']
    inlines = ('floor',)
