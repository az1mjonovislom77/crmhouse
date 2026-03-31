from django.contrib import admin
from home.models import Home
from projects.models.project_models import Projects, Blocks, Floors, Renovation
from projects.models.showroom_models import SVG


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


@admin.register(SVG)
class SVGAdmin(admin.ModelAdmin):
    list_display = ['id']
