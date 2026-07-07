
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0010_alter_booking_down_payment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='down_payment',
            field=models.IntegerField(blank=True, choices=[(0, '0'), (10, '10%'), (20, '20%'), (30, '30%'), (40, '40%'), (50, '50%')], null=True),
        ),
    ]
