
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0007_client_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='birth_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='jshshir',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='short_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
