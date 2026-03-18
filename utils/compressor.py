import sys
from io import BytesIO
from PIL import Image
import pillow_heif
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

pillow_heif.register_heif_opener()


def optimize_image_to_webp(image_field, quality: int = 80, max_width=1200, ) -> ContentFile:
    img = Image.open(image_field)
    img = img.convert('RGB')

    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_height = int(float(img.height) * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format='WEBP', quality=quality)
    buffer.seek(0)

    file_name = image_field.name.rsplit('.', 1)[0] + '.webp'
    new_image = InMemoryUploadedFile(buffer, 'ImageField', file_name, 'image/webp', sys.getsizeof(buffer), None)

    return new_image


def check_image_size(image):
    if image.size > 10 * 1024 * 1024:
        raise ValidationError("The image is too long")
