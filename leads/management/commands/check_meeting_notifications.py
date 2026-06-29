from django.core.management.base import BaseCommand
from leads.services.notification_service import MeetingNotificationService


class Command(BaseCommand):
    help = 'Yaqinlashayotgan uchrashuvlar uchun notification yaratadi (har 5 daqiqada cron orqali ishlatiladi)'

    def handle(self, *args, **options):
        created = MeetingNotificationService.check_and_create()
        if created:
            self.stdout.write(self.style.SUCCESS(f'{created} ta yangi notification yaratildi'))
        else:
            self.stdout.write('Yangi notification yo\'q')
