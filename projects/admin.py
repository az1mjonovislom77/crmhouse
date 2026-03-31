from django.contrib import admin
from home.models import Home
from projects.models import Projects, Blocks, Floors, Renovation


@admin.register(Projects)
class ProjectsAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']


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
