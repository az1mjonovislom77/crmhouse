
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0005_alter_home_entrance_alter_home_rooms'),
    ]

    operations = [
        migrations.AlterField(
            model_name='home',
            name='entrance',
            field=models.IntegerField(choices=[(1, '1 p'), (2, '2 p'), (3, '3 p'), (4, '4 p'), (5, '5 p'), (6, '6 p'), (7, '7 p'), (8, '8 p'), (9, '9 p'), (10, '10 p')], db_index=True, default=1),
        ),
        migrations.AlterField(
            model_name='home',
            name='home_status',
            field=models.CharField(choices=[('available', 'Available'), ('reserved', 'Reserved'), ('sold', 'Sold'), ('kalit_topshirildi', 'Kalit Topshirildi'), ('nomiga_otkazib_berildi', 'Nomiga O`tkazib Berildi')], db_index=True, default='available'),
        ),
    ]
