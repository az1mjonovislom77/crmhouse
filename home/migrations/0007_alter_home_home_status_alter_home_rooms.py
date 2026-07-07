
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_alter_home_entrance_alter_home_home_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='home',
            name='home_status',
            field=models.CharField(choices=[('available', 'Available'), ('reserved', 'Reserved'), ('sold', 'Sold'), ('kalit_topshirildi', 'Kalit Topshirildi'), ('nomiga_otkazib_berildi', 'Nomiga O`tkazib Berildi')], db_index=True, default='available', max_length=30),
        ),
        migrations.AlterField(
            model_name='home',
            name='rooms',
            field=models.IntegerField(choices=[(1, '1 xona'), (2, '2 xona'), (3, '3 xona'), (4, '4 xona'), (5, '5 xona'), (6, '6 xona'), (7, '7 xona'), (8, '8 xona'), (9, '9 xona'), (10, '10 xona')], db_index=True, default=1),
        ),
    ]
