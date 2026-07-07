from django.db import migrations


def seed_defaults(apps, schema_editor):
    CalculatorConfig = apps.get_model('calculator', 'CalculatorConfig')
    GuaranteeOption = apps.get_model('calculator', 'GuaranteeOption')
    SubsidyOption = apps.get_model('calculator', 'SubsidyOption')

    CalculatorConfig.objects.update_or_create(
        pk=1,
        defaults={
            'annual_rate_pct': 17,
            'state_threshold_pct': 14,
            'subsidy_years': 5,
            'firm_markup_pct': 16,
            'round_step': 1000,
            'default_price_per_m2': 7700000,
            'term_options': [20, 15],
        },
    )

    guarantees = [
        {'key': 'kafillik', 'label': 'Kafillik 15%', 'percent': 15, 'order': 1},
        {'key': 'kafilsiz', 'label': 'Kafilsiz 20%', 'percent': 20, 'order': 2},
    ]
    for g in guarantees:
        GuaranteeOption.objects.update_or_create(key=g['key'], defaults=g)

    subsidies = [
        {'key': 'yoq', 'label': "Yo'q", 'amount': 0, 'order': 1},
        {'key': 'oddiy', 'label': 'Oddiy', 'amount': 30000000, 'order': 2},
    ]
    for s in subsidies:
        SubsidyOption.objects.update_or_create(key=s['key'], defaults=s)


def unseed(apps, schema_editor):
    apps.get_model('calculator', 'GuaranteeOption').objects.all().delete()
    apps.get_model('calculator', 'SubsidyOption').objects.all().delete()
    apps.get_model('calculator', 'CalculatorConfig').objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('calculator', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_defaults, unseed),
    ]
