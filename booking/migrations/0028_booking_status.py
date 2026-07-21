
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0027_backfill_booking_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('canceled', 'Canceled')], db_index=True, default='active', max_length=20),
        ),
    ]
