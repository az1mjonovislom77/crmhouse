
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0008_homestatushistory'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='home',
            name='basement',
        ),
    ]
