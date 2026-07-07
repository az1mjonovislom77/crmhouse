
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0018_booking_organization'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='organization',
        ),
    ]
