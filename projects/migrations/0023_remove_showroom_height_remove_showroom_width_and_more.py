
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0022_showroom_height_showroom_width'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='showroom',
            name='height',
        ),
        migrations.RemoveField(
            model_name='showroom',
            name='width',
        ),
        migrations.AddField(
            model_name='showroomimage',
            name='height',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='showroomimage',
            name='width',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
