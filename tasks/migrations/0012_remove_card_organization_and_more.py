
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0011_card_organization_historicalcard_organization_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='card',
            name='organization',
        ),
        migrations.RemoveField(
            model_name='historicalcard',
            name='organization',
        ),
    ]
