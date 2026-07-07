
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0023_remove_booking_cash_payment_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PaymentTerm',
        ),
    ]
