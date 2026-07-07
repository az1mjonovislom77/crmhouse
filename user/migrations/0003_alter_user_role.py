
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_alter_user_phone_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(blank=True, choices=[('s', 'saler'), ('a', 'admin'), ('m', 'manager')], max_length=10, null=True),
        ),
    ]
