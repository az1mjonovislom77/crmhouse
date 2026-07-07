
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contact_center', '0002_callrecord_organization'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='callrecord',
            name='organization',
        ),
    ]
