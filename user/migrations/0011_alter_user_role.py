
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0010_user_organization_alter_user_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('s', 'SELLER'), ('sa', 'SUPERADMIN'), ('a', 'ADMIN')], default='s', max_length=10),
        ),
    ]
