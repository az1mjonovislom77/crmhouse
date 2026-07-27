from django.contrib import admin

from tasks.models import Card, Comment, Project


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ["id", "title"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["id", "title"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["id", "user"]
    list_select_related = ["user", "project"]
