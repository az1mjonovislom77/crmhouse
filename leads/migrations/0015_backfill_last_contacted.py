from django.db import migrations, models
from django.db.models import Max


def backfill_last_contacted(apps, schema_editor):
    Lead = apps.get_model('leads', 'Lead')
    LeadEvent = apps.get_model('leads', 'LeadEvent')

    leads = (
        Lead.objects.filter(last_contacted__isnull=True)
        .annotate(
            last_event=Max(
                'events__at',
                filter=models.Q(events__type__in=['comment', 'call']),
            )
        )
        .exclude(last_event__isnull=True)
    )
    for lead in leads:
        lead.last_contacted = lead.last_event
        lead.save(update_fields=['last_contacted'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0014_lead_last_contacted'),
    ]

    operations = [
        migrations.RunPython(backfill_last_contacted, noop),
    ]
