from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from leads.models import BOARD_FIRST_STATUS, BOARD_STATUSES, STATUS_NEW, STATUS_TOPSHIRIQLAR, Lead, LeadEvent


def _compute_score(lead):
    score = 0
    source_scores = {
        'Tavsiya': 20, 'Instagram': 15, 'Telegram': 15,
        'Facebook': 12, 'LinkedIn': 12, 'Veb-sayt': 10, "Qo'ng'iroq": 8,
    }
    score += source_scores.get(lead.source, 5)
    if lead.note:
        score += 5
    status_order = list(BOARD_STATUSES.get(lead.board, {}).keys())
    if lead.status in status_order:
        score += int((status_order.index(lead.status) / max(len(status_order) - 1, 1)) * 50)
    score += min(lead.events.count() * 2, 10)
    return min(score, 100)


class LeadService:

    @staticmethod
    @transaction.atomic
    def create_lead(data, user):
        board = data['board']
        meeting_at = data.pop('meeting_at', None)
        meeting_type = data.pop('meeting_type', None)
        status = BOARD_FIRST_STATUS[board]
        sub = BOARD_STATUSES[board][status][0]
        lead = Lead.objects.create(
            **data, owner=user, assignee=user, status=status, sub_status=sub, score=0,
            meeting_at=meeting_at, meeting_type=meeting_type,
        )
        LeadEvent.objects.create(lead=lead, type=LeadEvent.TYPE_CREATED, by=user)
        if meeting_at and meeting_type:
            LeadEvent.objects.create(
                lead=lead, type=LeadEvent.TYPE_MEETING,
                meeting_at=meeting_at, meeting_type=meeting_type, by=user,
            )
        lead.score = _compute_score(lead)
        lead.save(update_fields=['score'])
        return lead

    @staticmethod
    @transaction.atomic
    def update_lead(instance, data, user):
        comment = data.pop('comment', None)
        call_result = data.pop('call_result', None)
        meeting_at = data.pop('meeting_at', None)
        meeting_type = data.pop('meeting_type', None)
        new_status = data.pop('status', None)
        new_sub = data.pop('sub_status', None)
        data.pop('owner', None)
        new_assignee = data.pop('assignee', None)
        new_subsidiya = data.pop('subsidiya', None)

        for attr, value in data.items():
            setattr(instance, attr, value)

        board_statuses = BOARD_STATUSES.get(instance.board, {})

        if new_status and new_status != instance.status:
            if new_status not in board_statuses:
                raise ValidationError({'status': f"'{new_status}' bu board uchun yaroqli emas"})
            LeadEvent.objects.create(
                lead=instance, type=LeadEvent.TYPE_STATUS,
                from_value=instance.status, to_value=new_status, by=user,
            )
            instance.status = new_status
            if new_sub and new_sub in board_statuses[new_status]:
                instance.sub_status = new_sub
            else:
                instance.sub_status = board_statuses[new_status][0] if board_statuses[new_status] else None

        elif new_sub and new_sub != instance.sub_status:
            if new_sub not in board_statuses.get(instance.status, []):
                raise ValidationError({'sub_status': f"'{new_sub}' bu status uchun yaroqli emas"})
            LeadEvent.objects.create(
                lead=instance, type=LeadEvent.TYPE_SUB_STATUS,
                from_value=instance.sub_status, to_value=new_sub, by=user,
            )
            instance.sub_status = new_sub

        if new_assignee and new_assignee != instance.assignee:
            LeadEvent.objects.create(
                lead=instance, type=LeadEvent.TYPE_TRANSFER,
                from_value=instance.assignee.full_name if instance.assignee else '',
                to_value=new_assignee.full_name, by=user,
            )
            instance.assignee = new_assignee
            if instance.board == Lead.BOARD_SALES:
                if new_assignee != instance.owner:
                    if instance.status != STATUS_TOPSHIRIQLAR:
                        LeadEvent.objects.create(
                            lead=instance, type=LeadEvent.TYPE_STATUS,
                            from_value=instance.status, to_value=STATUS_TOPSHIRIQLAR, by=user,
                        )
                    instance.status = STATUS_TOPSHIRIQLAR
                    instance.sub_status = board_statuses[STATUS_TOPSHIRIQLAR][0]
                elif instance.status == STATUS_TOPSHIRIQLAR:
                    LeadEvent.objects.create(
                        lead=instance, type=LeadEvent.TYPE_STATUS,
                        from_value=instance.status, to_value=STATUS_NEW, by=user,
                    )
                    instance.status = STATUS_NEW
                    instance.sub_status = board_statuses[STATUS_NEW][0]

        if comment:
            LeadEvent.objects.create(lead=instance, type=LeadEvent.TYPE_COMMENT, text=comment, by=user)
            instance.last_contacted = timezone.now()

        if call_result:
            LeadEvent.objects.create(lead=instance, type=LeadEvent.TYPE_CALL, text=call_result, by=user)
            instance.last_contacted = timezone.now()

        if new_subsidiya is not None and new_subsidiya != instance.subsidiya:
            LeadEvent.objects.create(
                lead=instance, type=LeadEvent.TYPE_SUBSIDIYA,
                from_value=str(instance.subsidiya), to_value=str(new_subsidiya),
                subsidiya=new_subsidiya, by=user,
            )
            instance.subsidiya = new_subsidiya

        if meeting_at and meeting_type:
            LeadEvent.objects.create(lead=instance, type=LeadEvent.TYPE_MEETING,
                                     meeting_at=meeting_at, meeting_type=meeting_type, by=user)
            instance.meeting_at = meeting_at
            instance.meeting_type = meeting_type
            if instance.board == Lead.BOARD_SALES and instance.status != 'uchrashuv':
                LeadEvent.objects.create(
                    lead=instance, type=LeadEvent.TYPE_STATUS,
                    from_value=instance.status, to_value='uchrashuv', by=user,
                )
                instance.status = 'uchrashuv'
                instance.sub_status = board_statuses.get('uchrashuv', [None])[0]

        instance.score = _compute_score(instance)
        instance.save()
        return instance

    @staticmethod
    @transaction.atomic
    def bulk_assign_leads(lead_ids, assignee_to, user, queryset):
        leads = list(queryset.filter(pk__in=lead_ids))
        found_ids = {lead.pk for lead in leads}
        missing = set(lead_ids) - found_ids
        if missing:
            raise ValidationError({
                'lead_ids': f"Leadlar topilmadi yoki ruxsat yo'q: {sorted(missing)}",
            })

        updated_ids = []
        for lead in leads:
            LeadService.update_lead(lead, {'assignee': assignee_to}, user)
            updated_ids.append(lead.pk)
        return updated_ids
