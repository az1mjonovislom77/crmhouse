from django.contrib import admin
from utils.models import Blocks, Floors, Renovation, Basement


@admin.register(Blocks)
class BlocksAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']


@admin.register(Floors)
class FloorsAdmin(admin.ModelAdmin):
    list_display = ['id', 'number']


@admin.register(Renovation)
class RenovationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']


@admin.register(Basement)
class BasementAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']
