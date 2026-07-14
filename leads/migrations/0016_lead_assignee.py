from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def backfill_assignee(apps, schema_editor):
    Lead = apps.get_model('leads', 'Lead')
    Lead.objects.filter(
        assignee__isnull=True,
        owner__isnull=False,
    ).update(assignee_id=models.F('owner_id'))


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('leads', '0015_backfill_last_contacted'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='assignee',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assigned_leads',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(backfill_assignee, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['assignee'], name='leads_lead_assignee_idx'),
        ),
    ]
