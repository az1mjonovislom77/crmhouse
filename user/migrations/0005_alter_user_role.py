
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_alter_user_options_user_created_at_user_updated_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('s', 'SELLER'), ('c', 'CASHIER'), ('m', 'MANAGER'), ('w', 'WAREHOUSEMAN')], default='s', max_length=10),
        ),
    ]
