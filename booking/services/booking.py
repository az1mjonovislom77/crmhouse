from django.db import transaction
from rest_framework.exceptions import ValidationError

from booking.models import Booking, Company
from home.models import Home, HomeStatusHistory
from home.services.home import HomeService


@transaction.atomic
def create_booking(data, user=None, home_status=None):
    data = data.copy()

    home = data.get("home")
    if home is not None:
        home = Home.objects.select_for_update().get(pk=home.pk)
        data["home"] = home
        if Booking.objects.filter(home=home, status=Booking.BookingStatus.ACTIVE).exists():
            raise ValidationError({"home": "Bu uy allaqachon band qilingan."})
        # naqd sotuv (kalkulyator ishlamagan): contract_price'ni uy narxi + remontdan to'ldiramiz,
        # shunda contract_price va total_price har doim bir xil bo'ladi.
        if not data.get("contract_price"):
            reno = home.renovation.price if home.renovation else 0
            data["contract_price"] = (home.price_per_sqm or 0) * (home.area or 0) + reno

    if not data.get("company"):
        company = Company.objects.only("id").order_by("id").first()
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
def set_booking_status(booking_id, new_status, user=None):
    valid = {choice.value for choice in Booking.BookingStatus}
    if new_status not in valid:
        raise ValidationError({"status": f"Noto'g'ri status. Ruxsat etilganlar: {', '.join(sorted(valid))}."})

    booking = Booking.objects.select_related('home', 'client').get(id=booking_id)
    if booking.status == new_status:
        return booking

    home = Home.objects.select_for_update().get(id=booking.home_id)

    if new_status == Booking.BookingStatus.ACTIVE:
        other_active = (Booking.objects
                        .filter(home=home, status=Booking.BookingStatus.ACTIVE)
                        .exclude(pk=booking.pk)
                        .exists())
        if other_active:
            raise ValidationError({"home": "Bu uyda allaqachon aktiv booking mavjud."})

    booking.status = new_status
    booking.save(update_fields=["status"])

    if new_status == Booking.BookingStatus.CANCELED:
        if not Booking.objects.filter(home=home, status=Booking.BookingStatus.ACTIVE).exists():
            HomeService.change_status(
                home_id=home.id, new_status=Home.HomeStatus.AVAILABLE, user=user, client=booking.client)
    elif new_status == Booking.BookingStatus.ACTIVE:
        if home.home_status == Home.HomeStatus.AVAILABLE:
            HomeService.change_status(
                home_id=home.id, new_status=Home.HomeStatus.RESERVED, user=user, client=booking.client)

    return booking


@transaction.atomic
def delete_booking(booking_id, user=None):
    booking = Booking.objects.select_related('home', 'client').get(id=booking_id)

    if booking.payments.exists():
        raise ValidationError(
            {"detail": "Bu bookingda to'lovlar mavjud. Avval to'lovlar bilan bog'liq masalani hal qiling."})

    home = Home.objects.select_for_update().get(id=booking.home_id)
    client = booking.client

    booking.delete()

    HomeStatusHistory.objects.create(
        home=home, client=client, from_status=home.home_status,
        to_status="booking_deleted", changed_by=user
    )

    if not Booking.objects.filter(home=home, status=Booking.BookingStatus.ACTIVE).exists():
        HomeService.change_status(home_id=home.id, new_status=Home.HomeStatus.AVAILABLE, user=user, client=client)
