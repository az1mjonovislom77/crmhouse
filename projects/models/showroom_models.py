from django.core.validators import FileExtensionValidator
from django.db import models

from common.services.image_service import check_image_size, optimize_image_to_webp
from projects.models.project_models import Block


class SVG(models.Model):
    image = models.JSONField()

    def __str__(self):
        return str(self.id)


class ShowroomImage(models.Model):
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    image = models.ImageField(
        upload_to="showroom_images/",
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp", "heic", "heif"]),
            check_image_size,
        ],
    )

    def __str__(self):
        return f"ShowroomImage {self.pk}"

    def save(self, *args, **kwargs):
        if self.pk:
            old = ShowroomImage.objects.only("image").filter(pk=self.pk).first()
            if old and old.image == self.image:
                super().save(*args, **kwargs)
                return

        if self.image and not self.image.name.lower().endswith(".webp"):
            optimized_image = optimize_image_to_webp(self.image, quality=80)
            self.image.save(optimized_image.name, optimized_image, save=False)

        super().save(*args, **kwargs)


class Showroom(models.Model):
    image = models.ForeignKey(ShowroomImage, on_delete=models.CASCADE, null=True, blank=True, related_name="showrooms")
    title = models.CharField(max_length=200, null=True, blank=True)
    block = models.ForeignKey(Block, on_delete=models.SET_NULL, null=True, blank=True, related_name="showrooms")
    blocks_number = models.IntegerField(default=0)
    path = models.CharField(max_length=2000)
    navigate_to = models.CharField(max_length=200)
    hover_color = models.CharField(max_length=200)
    default_color = models.CharField(max_length=200)

    def __str__(self):
        return str(self.title)
