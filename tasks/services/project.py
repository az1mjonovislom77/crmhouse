from django.db import transaction
from django.db.models import F, Max
from tasks.models import Project, Card
from rest_framework.exceptions import ValidationError


def _shift_orders(qs, *, delta):
    project_ids = list(qs.values_list('id', flat=True))
    if not project_ids:
        return []

    max_order = Project.objects.aggregate(max_order=Max('order'))['max_order'] or 0
    offset = max_order + len(project_ids) + abs(delta) + 1

    Project.objects.filter(id__in=project_ids).update(order=F('order') + offset)
    Project.objects.filter(id__in=project_ids).update(order=F('order') - offset + delta)

    return project_ids


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

            _shift_orders(qs.filter(order__gte=order), delta=1)
        project = Project.objects.create(card=card, order=order, **data)

        if users is not None:
            project.users.set(users)

        return project


def update_project(project, *, new_card=None, new_order=None, users=None, **data):
    with transaction.atomic():
        updated_ids = set()

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

            return [{"id": project.id, "order": project.order, "card": project.card_id}]

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

        project.order = 0
        project.save(update_fields=['order'])

        if old_card == new_card:
            if new_order > old_order:
                ids = _shift_orders(old_qs.filter(order__gt=old_order, order__lte=new_order), delta=-1)
                updated_ids.update(ids)

            elif new_order < old_order:
                ids = _shift_orders(old_qs.filter(order__gte=new_order, order__lt=old_order), delta=1)
                updated_ids.update(ids)

        else:
            ids = _shift_orders(old_qs.filter(order__gt=old_order), delta=-1)
            updated_ids.update(ids)

            ids = _shift_orders(new_qs.filter(order__gte=new_order), delta=1)
            updated_ids.update(ids)

        for key, value in data.items():
            setattr(project, key, value)

        project.card = new_card
        project.order = new_order
        project.save()

        if users is not None:
            project.users.set(users)

        updated_ids.add(project.id)

        updated_projects = Project.objects.filter(id__in=updated_ids).values('id', 'order', 'card_id')

        return list(updated_projects)


def delete_project(project):
    with transaction.atomic():
        card = project.card
        order = project.order

        qs = Project.objects.select_for_update().filter(card=card)
        qs.filter(order__gt=order).update(order=F('order') - 1)

        project.delete()
