
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0014_remove_booking_from_who'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='payment_data',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_number',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
