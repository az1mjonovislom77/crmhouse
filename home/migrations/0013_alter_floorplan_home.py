
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0012_alter_floorplan_home'),
    ]

    operations = [
        migrations.AlterField(
            model_name='floorplan',
            name='home',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='plans', to='home.home'),
        ),
    ]
