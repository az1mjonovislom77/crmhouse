from django.conf import settings
from django.db import migrations, models


def forwards(apps, schema_editor):
    Organization = apps.get_model("organization", "Organization")
    Booking = apps.get_model("booking", "Booking")

    org_name = getattr(settings, "PAXTAZOR_ORG_NAME", "Paxtazor Xonadonlar")
    org_id = Organization.objects.filter(name=org_name).values_list("id", flat=True).first()
    if org_id is None:
        return

    bookings = (
        Booking.objects.filter(organization_id=org_id, status="active")
        .order_by("created_at", "id")
        .only("id", "paxtazor_no")
    )
    for number, booking in enumerate(bookings, start=1):
        if booking.paxtazor_no != number:
            booking.paxtazor_no = number
            booking.save(update_fields=["paxtazor_no"])


def backwards(apps, schema_editor):
    Booking = apps.get_model("booking", "Booking")
    Booking.objects.exclude(paxtazor_no=None).update(paxtazor_no=None)


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0033_commitment'),
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='paxtazor_no',
            field=models.PositiveIntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.AddConstraint(
            model_name='booking',
            constraint=models.UniqueConstraint(
                condition=models.Q(('paxtazor_no__isnull', False), ('status', 'active')),
                fields=('organization', 'paxtazor_no'),
                name='unique_active_paxtazor_no_per_org',
            ),
        ),
    ]
