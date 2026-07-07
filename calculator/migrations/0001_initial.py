
import calculator.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CalculatorConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annual_rate_pct', models.DecimalField(decimal_places=2, default=17, max_digits=5)),
                ('state_threshold_pct', models.DecimalField(decimal_places=2, default=14, max_digits=5)),
                ('subsidy_years', models.PositiveIntegerField(default=5)),
                ('firm_markup_pct', models.DecimalField(decimal_places=2, default=16, max_digits=5)),
                ('round_step', models.PositiveIntegerField(default=1000)),
                ('default_price_per_m2', models.DecimalField(decimal_places=2, default=7700000, max_digits=14)),
                ('term_options', models.JSONField(default=calculator.models.default_term_options)),
            ],
            options={
                'verbose_name': 'Kalkulyator sozlamasi',
                'verbose_name_plural': 'Kalkulyator sozlamalari',
            },
        ),
        migrations.CreateModel(
            name='GuaranteeOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=50, unique=True)),
                ('label', models.CharField(max_length=100)),
                ('percent', models.DecimalField(decimal_places=2, max_digits=5)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='SubsidyOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=50, unique=True)),
                ('label', models.CharField(max_length=100)),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
    ]
