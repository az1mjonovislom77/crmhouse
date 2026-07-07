
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0006_client_user'),
        ('home', '0018_alter_floorplan_image'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='homestatushistory',
            name='changed_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AddIndex(
            model_name='homestatushistory',
            index=models.Index(fields=['to_status', 'changed_at'], name='home_homest_to_stat_deb423_idx'),
        ),
    ]
