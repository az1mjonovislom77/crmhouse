from django.db import transaction
from rest_framework.exceptions import ValidationError
from booking.models import Booking, Company
from home.models import Home, HomeStatusHistory
from home.services.home import HomeService


@transaction.atomic
def create_booking(data, user=None, home_status=None):
    data = data.copy()

    if not data.get("company"):
        company = Company.objects.order_by("id").first()
        if not company:
            raise ValidationError("Company hali yaratilmagan")
        data["company"] = company

    booking = Booking.objects.create(**data)

    if home_status:
        HomeService.change_status(
            home_id=booking.home.id,
            new_status=home_status,
            user=user,
            client=booking.client)

    return booking


@transaction.atomic
def delete_booking(booking_id, user=None):
    booking = Booking.objects.select_related('home', 'client').get(id=booking_id)
    home = Home.objects.select_for_update().get(id=booking.home_id)

    client = booking.client

    booking.delete()

    HomeStatusHistory.objects.create(
        home=home,
        client=client,
        from_status=home.home_status,
        to_status="booking_deleted",
        changed_by=user
    )

    if not Booking.objects.filter(home=home).exists():
        HomeService.change_status(home_id=home.id, new_status=Home.HomeStatus.AVAILABLE, user=user, client=client)
