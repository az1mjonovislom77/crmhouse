
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0015_alter_block_image_alter_project_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='showroom',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='showroom/'),
        ),
    ]
