from django.db import transaction
from django.db.models import F, Max
from tasks.models import Project, Card
from rest_framework.exceptions import ValidationError


def create_project(*, card=None, users=None, order=None, **data):
    with transaction.atomic():
        if card is None:
            card = Card.objects.order_by('id').first()
            if not card:
                raise ValidationError("Card mavjud emas! Avval card yarating")

        qs = Project.objects.select_for_update().filter(card=card)

        max_order = qs.aggregate(max_order=Max('order'))['max_order'] or 0

        if order is None or order > max_order:
            order = max_order + 1
        else:
            if order < 1:
                order = 1

            qs.filter(order__gte=order).update(order=F('order') + 1)
        project = Project.objects.create(card=card, order=order, **data)

        if users is not None:
            project.users.set(users)

        return project


def update_project(project, *, new_card=None, new_order=None, users=None, **data):
    with transaction.atomic():
        old_card = project.card
        old_order = project.order

        new_card = new_card or old_card
        new_order = new_order if new_order is not None else old_order

        if new_card == old_card and new_order == old_order:
            for key, value in data.items():
                setattr(project, key, value)

            project.save()

            if users is not None:
                project.users.set(users)

            return project

        card_ids = sorted([old_card.id, new_card.id])

        qs1 = Project.objects.select_for_update().filter(card_id=card_ids[0])
        qs2 = Project.objects.select_for_update().filter(card_id=card_ids[1])

        old_qs = qs1 if old_card.id == card_ids[0] else qs2
        new_qs = qs2 if new_card.id == card_ids[1] else qs1

        max_order = new_qs.aggregate(max_order=Max('order'))['max_order'] or 0

        if new_order > max_order:
            new_order = max_order + 1
        elif new_order < 1:
            new_order = 1

        if old_card == new_card:
            if new_order > old_order:
                old_qs.filter(order__gt=old_order, order__lte=new_order).update(order=F('order') - 1)

            elif new_order < old_order:
                old_qs.filter(order__gte=new_order, order__lt=old_order).update(order=F('order') + 1)

        else:
            old_qs.filter(order__gt=old_order).update(order=F('order') - 1)
            new_qs.filter(order__gte=new_order).update(order=F('order') + 1)

        for key, value in data.items():
            setattr(project, key, value)

        project.card = new_card
        project.order = new_order
        project.save()

        if users is not None:
            project.users.set(users)

        return project


def delete_project(project):
    with transaction.atomic():
        card = project.card
        order = project.order

        qs = Project.objects.select_for_update().filter(card=card)
        qs.filter(order__gt=order).update(order=F('order') - 1)

        project.delete()
