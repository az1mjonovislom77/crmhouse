
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0013_remove_lead_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='last_contacted',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
