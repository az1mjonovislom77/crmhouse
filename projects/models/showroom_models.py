from django.db import models
from projects.models.project_models import Block


class SVG(models.Model):
    image = models.JSONField()

    def __str__(self):
        return str(self.id)


class Showroom(models.Model):
    block = models.ForeignKey(Block, on_delete=models.SET_NULL, null=True, blank=True, related_name='showrooms')
    blocks_number = models.IntegerField(default=0)
    path = models.CharField(max_length=500)
    navigate_to = models.CharField(max_length=200)
    hover_color = models.CharField(max_length=200)
    default_color = models.CharField(max_length=200)

    def __str__(self):
        return str(self.id)
