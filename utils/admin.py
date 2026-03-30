from django.contrib import admin

from home.models import Home
from utils.models import Blocks, Floors, Renovation


class HomeInline(admin.TabularInline):
    model = Home
    extra = 1


@admin.register(Blocks)
class BlocksAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']
    inlines = [HomeInline]


@admin.register(Floors)
class FloorsAdmin(admin.ModelAdmin):
    list_display = ['id', 'number']


@admin.register(Renovation)
class RenovationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']
