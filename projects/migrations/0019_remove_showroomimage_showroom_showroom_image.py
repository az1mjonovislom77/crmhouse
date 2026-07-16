
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0018_alter_showroomimage_showroom_showroom_title_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='showroomimage',
            name='showroom',
        ),
        migrations.AddField(
            model_name='showroom',
            name='image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='showrooms', to='projects.showroomimage'),
        ),
    ]
