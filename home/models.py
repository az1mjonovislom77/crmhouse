from django.core.validators import FileExtensionValidator
from django.db import models
from utils.compressor import optimize_image_to_webp, check_image_size
from utils.models import Blocks, Floors, Renovation, Basement


class Home(models.Model):
    class HomeStatus(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        RESERVED = 'reserved', 'Reserved'
        SOLD = 'sold', 'Sold'
        KALIT_TOPSHIRILDI = 'kalit_topshirildi', 'Kalit Topshirildi'
        NOMIGA_OTKAZIB_BERILDI = 'nomiga_otkazib_berildi', 'Nomiga O`tkazib Berildi'

    class EntranceChoice(models.IntegerChoices):
        ONE = 1, "1"
        TWO = 2, "2"
        THREE = 3, "3"
        FOUR = 4, "4"
        FIVE = 5, "5"
        SIX = 6, "6"
        SEVEN = 7, "7"
        EIGHT = 8, "8"
        NINE = 9, "9"
        TEN = 10, "10"

    class RoomsChoice(models.IntegerChoices):
        ONE = 1, "1"
        TWO = 2, "2"
        THREE = 3, "3"
        FOUR = 4, "4"
        FIVE = 5, "5"
        SIX = 6, "6"
        SEVEN = 7, "7"
        EIGHT = 8, "8"
        NINE = 9, "9"
        TEN = 10, "10"

    home_number = models.PositiveIntegerField(default=0)
    blocks = models.ForeignKey(Blocks, on_delete=models.SET_NULL, null=True, blank=True, related_name='homes')
    floor = models.ForeignKey(Floors, on_delete=models.SET_NULL, null=True, blank=True)
    rooms = models.CharField(choices=RoomsChoice.choices, default=RoomsChoice.ONE, max_length=10, db_index=True)
    area = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    home_status = models.CharField(choices=HomeStatus.choices, default=HomeStatus.AVAILABLE, max_length=10,
                                   db_index=True)
    renovation = models.ForeignKey(Renovation, on_delete=models.SET_NULL, null=True, blank=True)
    basement = models.ForeignKey(Basement, on_delete=models.SET_NULL, null=True, blank=True)
    price_per_sqm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    entrance = models.CharField(choices=EntranceChoice.choices, default=EntranceChoice.ONE, max_length=10,
                                db_index=True)

    def __str__(self):
        return f"Home {self.home_number}"


class FloorPlan(models.Model):
    home = models.ForeignKey(Home, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.FileField(upload_to='projects/', validators=[
        FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'svg', 'webp', 'heic', 'heif']), check_image_size])

    def save(self, *args, **kwargs):
        if self.pk:
            old = FloorPlan.objects.only("image").filter(pk=self.pk).first()
            if old and old.image == self.image:
                super().save(*args, **kwargs)
                return

        if self.image and not self.image.name.lower().endswith(".webp"):
            optimized_image = optimize_image_to_webp(self.image, quality=80)
            self.image.save(optimized_image.name, optimized_image, save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        if self.home and self.home.title:
            return self.home.title
        return f"FloorPlan {self.pk}"
