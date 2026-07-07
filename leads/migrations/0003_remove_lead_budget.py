
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0002_alter_leadevent_by'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lead',
            name='budget',
        ),
    ]
