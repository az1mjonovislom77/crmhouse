from django.core.validators import FileExtensionValidator
from django.db import models

from common.services.image_service import check_image_size


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    logo = models.ImageField(upload_to='logo/',
                             validators=[FileExtensionValidator(
                                 allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'heic', 'heif']),
                                 check_image_size], null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organizations'
        ordering = ['name']

    def __str__(self):
        return self.name
