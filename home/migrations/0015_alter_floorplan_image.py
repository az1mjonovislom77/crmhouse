
import common.services.image_service
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0014_homestatushistory_client'),
    ]

    operations = [
        migrations.AlterField(
            model_name='floorplan',
            name='image',
            field=models.ImageField(upload_to='floor_plan/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg', 'webp', 'heic', 'heif']), common.services.image_service.check_image_size]),
        ),
    ]
