from django.contrib import admin
from projects.models import Projects


@admin.register(Projects)
class ProjectsAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']
