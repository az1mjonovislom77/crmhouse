from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from leads.models import LeadNotification
from leads.api.serializers import LeadNotificationSerializer
from leads.services.notification_service import MeetingNotificationService


@shared_task
def check_meeting_notifications():
    created_ids = MeetingNotificationService.check_and_create()
    if not created_ids:
        return 0

    channel_layer = get_channel_layer()
    notifications = LeadNotification.objects.filter(
        id__in=created_ids,
    ).select_related('lead', 'owner')

    for notif in notifications:
        data = LeadNotificationSerializer(notif).data
        async_to_sync(channel_layer.group_send)(
            f'notifications_{notif.owner_id}',
            {'type': 'send_notification', 'data': dict(data)},
        )

    return len(created_ids)
