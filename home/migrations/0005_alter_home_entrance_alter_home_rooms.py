
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_alter_home_entrance_alter_home_rooms'),
    ]

    operations = [
        migrations.AlterField(
            model_name='home',
            name='entrance',
            field=models.IntegerField(choices=[(1, '1 p'), (2, '2 p'), (3, '3 p'), (4, '4 p'), (5, '5 p'), (6, '6 p'), (7, '7 p'), (8, '8 p'), (9, '9 p'), (10, '10 p')], db_index=True, default=1, max_length=10),
        ),
        migrations.AlterField(
            model_name='home',
            name='rooms',
            field=models.IntegerField(choices=[(1, '1 xona'), (2, '2 xona'), (3, '3 xona'), (4, '4 xona'), (5, '5 xona'), (6, '6 xona'), (7, '7 xona'), (8, '8 xona'), (9, '9 xona'), (10, '10 xona')], db_index=True, default=1, max_length=10),
        ),
    ]
