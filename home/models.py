from django.core.validators import FileExtensionValidator
from django.db import models
from django.conf import settings

from projects.models.project_models import Blocks, Floors, Renovation


class Home(models.Model):
    class HomeStatus(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        RESERVED = 'reserved', 'Reserved'
        SOLD = 'sold', 'Sold'
        KALIT_TOPSHIRILDI = 'kalit_topshirildi', 'Kalit Topshirildi'
        NOMIGA_OTKAZIB_BERILDI = 'nomiga_otkazib_berildi', 'Nomiga O`tkazib Berildi'

    class EntranceChoice(models.IntegerChoices):
        ONE = 1, "1 p"
        TWO = 2, "2 p"
        THREE = 3, "3 p"
        FOUR = 4, "4 p"
        FIVE = 5, "5 p"
        SIX = 6, "6 p"
        SEVEN = 7, "7 p"
        EIGHT = 8, "8 p"
        NINE = 9, "9 p"
        TEN = 10, "10 p"

    class RoomsChoice(models.IntegerChoices):
        ONE = 1, "1 xona"
        TWO = 2, "2 xona"
        THREE = 3, "3 xona"
        FOUR = 4, "4 xona"
        FIVE = 5, "5 xona"
        SIX = 6, "6 xona"
        SEVEN = 7, "7 xona"
        EIGHT = 8, "8 xona"
        NINE = 9, "9 xona"
        TEN = 10, "10 xona"

    home_number = models.PositiveIntegerField(default=0)
    blocks = models.ForeignKey(Blocks, on_delete=models.SET_NULL, null=True, blank=True, related_name='homes')
    floor = models.ForeignKey(Floors, on_delete=models.SET_NULL, null=True, blank=True)
    rooms = models.IntegerField(choices=RoomsChoice.choices, default=RoomsChoice.ONE, db_index=True)
    area = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    home_status = models.CharField(choices=HomeStatus.choices, default=HomeStatus.AVAILABLE, max_length=30,
                                   db_index=True)
    renovation = models.ForeignKey(Renovation, on_delete=models.SET_NULL, null=True, blank=True)
    price_per_sqm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    entrance = models.IntegerField(choices=EntranceChoice.choices, default=EntranceChoice.ONE, db_index=True)

    def __str__(self):
        return f"Home {self.home_number}"


class HomeStatusHistory(models.Model):
    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=30, null=True, blank=True)
    to_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]


class FloorPlan(models.Model):
    home = models.ForeignKey(Home, on_delete=models.SET_NULL, null=True, blank=True)

    image = models.ImageField(upload_to='projects/',
                              validators=[FileExtensionValidator(
                                  allowed_extensions=['jpg', 'jpeg', 'png', 'svg', 'webp', 'heic', 'heif'])])

    def __str__(self):
        return f"FloorPlan {self.pk}"
