from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0004_lead_meeting_at_lead_meeting_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='subsidiya',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='leadevent',
            name='subsidiya',
            field=models.BooleanField(default=False),
        ),
    ]
