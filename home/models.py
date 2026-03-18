from django.core.validators import FileExtensionValidator
from django.db import models
from utils.compressor import optimize_image_to_webp, check_image_size
from utils.models import Blocks, Floors, Rooms, Renovation, Basement
from decimal import Decimal


class Home(models.Model):
    class HomeStatus(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        RESERVED = 'reserved', 'Reserved'
        SOLD = 'sold', 'Sold'

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

    title = models.CharField(max_length=100)
    blocks = models.ForeignKey(Blocks, on_delete=models.SET_NULL, null=True, blank=True, related_name='homes')
    floor = models.ForeignKey(Floors, on_delete=models.SET_NULL, null=True, blank=True)
    rooms = models.ForeignKey(Rooms, on_delete=models.SET_NULL, null=True, blank=True)
    area = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    home_status = models.CharField(choices=HomeStatus.choices, default=HomeStatus.AVAILABLE, max_length=10,
                                   db_index=True)
    renovation = models.ForeignKey(Renovation, on_delete=models.SET_NULL, null=True, blank=True)
    basement = models.ForeignKey(Basement, on_delete=models.SET_NULL, null=True, blank=True)
    price_per_sqm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    entrance = models.CharField(choices=EntranceChoice.choices, default=EntranceChoice.ONE, max_length=10,
                                db_index=True)

    @property
    def total_price(self):
        basement_price = self.basement.price if self.basement else Decimal("0")
        renovation_price = self.renovation.price if self.renovation else Decimal("0")

        return self.area * self.price_per_sqm + basement_price + renovation_price

    @property
    def initial_payment(self):
        booking = getattr(self, "booking", None)
        if not booking:
            return Decimal("0")
        return self.total_price * booking.down_payment / Decimal("100")

    @property
    def monthly_payment(self):
        booking = getattr(self, "booking", None)
        if not booking:
            return Decimal("0")

        total = self.total_price
        initial = total * booking.down_payment / Decimal("100")
        remaining = total - initial

        return remaining / booking.payment_term.months

    def __str__(self):
        return self.title


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
