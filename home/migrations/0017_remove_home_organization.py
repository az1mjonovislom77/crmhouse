
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0016_home_organization'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='home',
            name='organization',
        ),
    ]
