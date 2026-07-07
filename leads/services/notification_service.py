from django.db.models import F
from django.utils import timezone
from leads.models import Lead, LeadNotification


class MeetingNotificationService:

    @staticmethod
    def check_and_create():
        LeadNotification.objects.exclude(meeting_at=F('lead__meeting_at')).delete()

        today = timezone.now().date()
        upcoming = Lead.objects.filter(
            meeting_at__date=today,
            owner__isnull=False,
        ).select_related('owner')

        created_ids = []
        for lead in upcoming:
            obj, created = LeadNotification.objects.update_or_create(
                lead=lead, meeting_at=lead.meeting_at,
                defaults={'owner': lead.owner},
            )
            if created:
                created_ids.append(obj.id)

        return created_ids
