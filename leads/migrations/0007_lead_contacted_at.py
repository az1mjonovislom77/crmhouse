from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0006_alter_lead_source_alter_leadevent_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='contacted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
