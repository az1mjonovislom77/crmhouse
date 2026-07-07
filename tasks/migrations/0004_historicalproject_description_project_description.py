
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_alter_comment_project'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalproject',
            name='description',
            field=models.TextField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='description',
            field=models.TextField(default=1),
            preserve_default=False,
        ),
    ]
