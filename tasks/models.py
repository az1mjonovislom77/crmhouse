from django.db import models
from simple_history.models import HistoricalRecords
from common.base.models_base import TimeStampedModel
from config import settings


class Card(TimeStampedModel):
    title = models.CharField(max_length=200)

    history = HistoricalRecords()

    def __str__(self):
        return self.title


class Project(TimeStampedModel):
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='task_projects', blank=True)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.PositiveIntegerField()
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(
                fields=['card', 'order'], name='unique_order_per_card'
            )
        ]
        indexes = [
            models.Index(fields=['card', 'order'], name='card_order_idx')
        ]

    def __str__(self):
        return self.title


class Comment(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    file = models.FileField(upload_to='comments/', null=True, blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.user} - {self.text[:15]}"
