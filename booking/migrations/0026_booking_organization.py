
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0025_remove_booking_rounding'),
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bookings', to='organization.organization'),
        ),
    ]
