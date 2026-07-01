from datetime import timedelta

from django.db import transaction

from common.utils import normalize_phone
from contact_center.models import CallRecord


class CallMatchingService:

    WINDOW_MINUTES = 10

    @classmethod
    def find_calls_for_appeal(cls, appeal):
        phone = normalize_phone(appeal.phone)

        if not phone:
            return CallRecord.objects.none()

        start = appeal.created_at - timedelta(minutes=cls.WINDOW_MINUTES)
        end = appeal.created_at + timedelta(minutes=cls.WINDOW_MINUTES)

        return CallRecord.objects.filter(
            src__endswith=phone,
            calldate__range=(start, end),
        )

    @classmethod
    @transaction.atomic
    def attach_calls(cls, appeal):
        # Requires 'appeals' app with AppealCallRecord model
        from django.apps import apps
        AppealCallRecord = apps.get_model('appeals', 'AppealCallRecord')

        calls = cls.find_calls_for_appeal(appeal)

        links = [
            AppealCallRecord(appeal=appeal, call_record=call)
            for call in calls
        ]

        AppealCallRecord.objects.bulk_create(links, ignore_conflicts=True)
        return len(links)
