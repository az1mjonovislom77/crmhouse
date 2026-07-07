
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_delete_basement_delete_rooms_blocks_projects_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SVG',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.JSONField()),
            ],
        ),
    ]
