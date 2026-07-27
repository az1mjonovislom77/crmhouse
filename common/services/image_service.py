from io import BytesIO

import pillow_heif
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image

pillow_heif.register_heif_opener()


def optimize_image_to_webp(
    image_field,
    quality: int = 80,
    max_width=1200,
) -> InMemoryUploadedFile:
    img: Image.Image = Image.open(image_field)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() or img.mode == "P" else "RGB")

    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_height = int(float(img.height) * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format="WEBP", quality=quality)
    size = buffer.getbuffer().nbytes
    buffer.seek(0)
    file_name = image_field.name.rsplit(".", 1)[0] + ".webp"
    new_image = InMemoryUploadedFile(buffer, "ImageField", file_name, "image/webp", size, None)

    return new_image


def check_image_size(file):
    if file.size > 15 * 1024 * 1024:
        raise ValidationError("Fayl hajmi 15 MB dan oshmasligi kerak")


def process_image(image):
    if not image:
        return image

    check_image_size(image)

    if not image.name.lower().endswith(".webp"):
        return optimize_image_to_webp(image, quality=80)

    return image
