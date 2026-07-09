from django.contrib import admin
from home.models import Home
from projects.models.project_models import Project, Block, Floors, Renovation
from projects.models.showroom_models import SVG, Showroom, ShowroomImage


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']


class HomeInline(admin.TabularInline):
    model = Home
    extra = 1


class ShowroomInline(admin.TabularInline):
    model = Showroom
    extra = 1


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
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


@admin.register(ShowroomImage)
class ShowroomImageAdmin(admin.ModelAdmin):
    list_display = ['id']
    inlines = [ShowroomInline]


@admin.register(Showroom)
class ShowroomAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'block', 'image']
