
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0008_leadnotification'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='leadnotification',
            name='is_read',
        ),
    ]
