
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0003_alter_client_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='passport_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
