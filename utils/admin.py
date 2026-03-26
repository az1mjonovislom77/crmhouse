from django.contrib import admin
from utils.models import Blocks, Floors, Renovation


@admin.register(Blocks)
class BlocksAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']


@admin.register(Floors)
class FloorsAdmin(admin.ModelAdmin):
    list_display = ['id', 'number']


@admin.register(Renovation)
class RenovationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']
