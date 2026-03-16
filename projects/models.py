from user.models import User
from django.db import models
from django.core.validators import FileExtensionValidator

from utils.compressor import check_image_size, optimize_image_to_webp


class Projects(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=100, db_index=True)
    description = models.TextField(max_length=500)
    floors = models.PositiveIntegerField(default=0)
    image = models.FileField(upload_to='projects/', validators=[
        FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'svg', 'webp', 'JPG', 'JPEG', 'PNG', 'SVG', 'WEBP', 'heic',
                                'heif']), check_image_size])
    rate = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.pk:
            old = Projects.objects.only("image").filter(pk=self.pk).first()
            if old and old.image == self.image:
                super().save(*args, **kwargs)
                return

        if self.image and not self.image.name.lower().endswith(".webp"):
            optimized_image = optimize_image_to_webp(self.image, quality=80)
            self.image.save(optimized_image.name, optimized_image, save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
