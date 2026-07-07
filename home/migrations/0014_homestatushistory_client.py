
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0001_initial'),
        ('home', '0013_alter_floorplan_home'),
    ]

    operations = [
        migrations.AddField(
            model_name='homestatushistory',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='status_history', to='client.client'),
        ),
    ]
