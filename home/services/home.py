from django.db import transaction

from booking.models import Booking
from home.models import Home, HomeStatusHistory
from home.services.floorplan_service import FloorPlanService


class HomeService:

    @staticmethod
    @transaction.atomic
    def create_home(data):
        floorplans = data.pop("floorplans", [])

        home = Home.objects.create(**data)

        for fp in floorplans:
            fp["home"] = home
            FloorPlanService.create_floorplan(fp)

        return home

    @staticmethod
    @transaction.atomic
    def update_home(instance, data):
        floorplans = data.pop("floorplans", None)

        for attr, value in data.items():
            setattr(instance, attr, value)

        instance.save()

        if floorplans is not None:
            instance.floorplan_set.all().delete()

            for fp in floorplans:
                fp["home"] = instance
                FloorPlanService.create_floorplan(fp)

        return instance

    @staticmethod
    @transaction.atomic
    def change_status(home_id, new_status, user=None, client=None):
        home = Home.objects.select_for_update().get(id=home_id)

        if home.home_status == new_status:
            return home

        old = home.home_status
        home.home_status = new_status
        home.save(update_fields=["home_status"])

        if not client:
            try:
                client = home.booking.client
            except Booking.DoesNotExist:
                client = None

        HomeStatusHistory.objects.create(
            home=home,
            client=client,
            from_status=old,
            to_status=new_status,
            changed_by=user
        )

        return home
