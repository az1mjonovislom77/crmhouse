
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0003_alter_booking_client'),
        ('client', '0001_initial'),
        ('home', '0009_remove_home_basement'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='client.client'),
        ),
        migrations.AlterField(
            model_name='booking',
            name='home',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='home.home'),
        ),
    ]
