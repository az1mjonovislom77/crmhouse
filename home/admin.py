from django.contrib import admin

from home.models import FloorPlan, Home, HomeStatusHistory


@admin.register(FloorPlan)
class FloorPlanAdmin(admin.ModelAdmin):
    list_display = ["id", "home"]
    list_select_related = ["home"]


class FloorPlanInline(admin.TabularInline):
    model = FloorPlan
    extra = 1


@admin.register(Home)
class HomeAdmin(admin.ModelAdmin):
    list_display = ["id", "home_number", "floor", "blocks"]
    list_filter = ("home_number", "floor", "blocks", "rooms")
    search_fields = ("id", "home_number", "blocks__title", "floor__number")
    list_select_related = ["floor", "blocks", "renovation"]
    inlines = [FloorPlanInline]


@admin.register(HomeStatusHistory)
class HomeStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ["id"]
