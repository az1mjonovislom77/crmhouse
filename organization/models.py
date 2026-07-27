from django.core.validators import FileExtensionValidator
from django.db import models

from common.services.image_service import check_image_size, optimize_image_to_webp


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    logo = models.ImageField(
        upload_to="logo/",
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp", "heic", "heif"]),
            check_image_size,
        ],
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "organizations"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk:
            old = Organization.objects.only("logo").filter(pk=self.pk).first()
            if old and old.logo == self.logo:
                super().save(*args, **kwargs)
                return

        if self.logo and not self.logo.name.lower().endswith(".webp"):
            optimized_image = optimize_image_to_webp(self.logo, quality=80)
            self.logo.save(optimized_image.name, optimized_image, save=False)

        super().save(*args, **kwargs)
