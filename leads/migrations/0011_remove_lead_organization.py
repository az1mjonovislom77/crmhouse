
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0010_lead_organization'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lead',
            name='organization',
        ),
    ]
