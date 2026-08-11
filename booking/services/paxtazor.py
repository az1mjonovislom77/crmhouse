from django.conf import settings
from django.db import transaction

DEFAULT_PAXTAZOR_ORG_NAME = "Paxtazor Xonadonlar"


def paxtazor_org_name():
    return getattr(settings, "PAXTAZOR_ORG_NAME", DEFAULT_PAXTAZOR_ORG_NAME)


def _lock_paxtazor_org(organization_id):
    from organization.models import Organization

    if organization_id is None:
        return False
    name = Organization.objects.select_for_update().filter(pk=organization_id).values_list("name", flat=True).first()
    return name == paxtazor_org_name()


def _taken_numbers(organization_id, exclude_pk=None):
    from booking.models import Booking

    qs = Booking.objects.filter(
        organization_id=organization_id,
        status=Booking.BookingStatus.ACTIVE,
        paxtazor_no__isnull=False,
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return set(qs.values_list("paxtazor_no", flat=True))


def _first_free(taken):
    number = 1
    while number in taken:
        number += 1
    return number


def resolve_paxtazor_no(booking):
    with transaction.atomic():
        if not _lock_paxtazor_org(booking.organization_id):
            return None
        taken = _taken_numbers(booking.organization_id, exclude_pk=booking.pk)
        if booking.paxtazor_no and booking.paxtazor_no not in taken:
            return booking.paxtazor_no
        return _first_free(taken)
