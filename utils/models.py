from django.db import models
from projects.models import Projects


class Blocks(models.Model):
    projects = models.ForeignKey(Projects, on_delete=models.SET_NULL, null=True, blank=True, related_name='blocks')
    title = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.title


class Floors(models.Model):
    number = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.number)


class Renovation(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.title
