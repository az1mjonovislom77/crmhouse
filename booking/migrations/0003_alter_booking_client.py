
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0002_remove_booking_address_remove_booking_full_name_and_more'),
        ('client', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking', to='client.client'),
        ),
    ]
