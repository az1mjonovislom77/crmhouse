
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0002_seed_defaults'),
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='calculatorconfig',
            options={},
        ),
        migrations.AddField(
            model_name='calculatorconfig',
            name='formula_key',
            field=models.CharField(choices=[('standart', 'Standart (annuitet)'), ('teng_ulush', 'Teng ulush (foizsiz)')], default='standart', max_length=30),
        ),
        migrations.AddField(
            model_name='calculatorconfig',
            name='organization',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='calculator_config', to='organization.organization'),
        ),
        migrations.AddField(
            model_name='guaranteeoption',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='guarantee_options', to='organization.organization'),
        ),
        migrations.AddField(
            model_name='subsidyoption',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subsidy_options', to='organization.organization'),
        ),
        migrations.AlterField(
            model_name='guaranteeoption',
            name='key',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='subsidyoption',
            name='key',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterUniqueTogether(
            name='guaranteeoption',
            unique_together={('organization', 'key')},
        ),
        migrations.AlterUniqueTogether(
            name='subsidyoption',
            unique_together={('organization', 'key')},
        ),
    ]
