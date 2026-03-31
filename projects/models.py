from core.services.image_service import check_image_size, optimize_image_to_webp
from user.models import User
from django.db import models
from django.core.validators import FileExtensionValidator


class Projects(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=100, db_index=True)
    description = models.TextField(max_length=500)
    floors = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='projects/', validators=[
        FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'svg', 'webp', 'JPG', 'JPEG', 'PNG', 'SVG', 'WEBP', 'heic',
                                'heif']), check_image_size], null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.title


class Blocks(models.Model):
    projects = models.ForeignKey(Projects, on_delete=models.SET_NULL, null=True, blank=True, related_name='blocks')
    title = models.CharField(max_length=100, db_index=True)
    image = models.FileField(upload_to='projects/', validators=[
        FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'svg', 'webp', 'heic', 'heif']), check_image_size])

    def save(self, *args, **kwargs):
        if self.pk:
            old = Blocks.objects.only("image").filter(pk=self.pk).first()
            if old and old.image == self.image:
                super().save(*args, **kwargs)
                return

        if self.image and not self.image.name.lower().endswith(".webp"):
            optimized_image = optimize_image_to_webp(self.image, quality=80)
            self.image.save(optimized_image.name, optimized_image, save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Floors(models.Model):
    number = models.IntegerField(default=0)

    def __str__(self):
        return str(self.number)


class Renovation(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.title
