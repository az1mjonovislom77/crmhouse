from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0024_delete_paymentterm'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='rounding',
        ),
    ]
