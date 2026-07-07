
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0015_payment_payment_data_payment_payment_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='payments/'),
        ),
    ]
