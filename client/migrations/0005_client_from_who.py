
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0004_client_passport_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='from_who',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
