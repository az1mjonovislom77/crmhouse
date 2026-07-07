
import django.db.models.deletion
import phonenumber_field.modelfields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('home', '0002_remove_home_title_home_home_number_alter_home_rooms'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentTerm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('months', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=100)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('passport', models.CharField(max_length=20)),
                ('address', models.CharField(max_length=250)),
                ('down_payment', models.IntegerField(choices=[(10, '10%'), (20, '20%'), (30, '30%'), (40, '40%'), (50, '50%')])),
                ('home', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='booking', to='home.home')),
                ('payment_term', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='booking.paymentterm')),
            ],
        ),
    ]
