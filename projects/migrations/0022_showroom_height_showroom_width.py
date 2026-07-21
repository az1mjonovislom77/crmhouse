
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0021_remove_block_image_blockimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='showroom',
            name='height',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='showroom',
            name='width',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
