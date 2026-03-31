from django.db import models


class SVG(models.Model):
    image = models.JSONField()

    def __str__(self):
        return str(self.id)
