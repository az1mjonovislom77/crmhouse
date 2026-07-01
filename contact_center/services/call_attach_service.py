import re

from django.db import transaction

from contact_center.models import CallRecord


class CallAttachService:

    @staticmethod
    def normalize(phone):
        if not phone:
            return ''
        return re.sub(r'\D', '', phone)

    @classmethod
    def attach_all(cls, batch_size=50):
        # Requires 'appeals' app with Appeal and AppealCallRecord models
        from django.apps import apps
        Appeal = apps.get_model('appeals', 'Appeal')
        AppealCallRecord = apps.get_model('appeals', 'AppealCallRecord')

        appeals = Appeal.objects.filter(
            channel=Appeal.Channel.CALL,
            phone__isnull=False,
        ).order_by('id')

        total = appeals.count()
        print(f'Total appeals: {total}')

        processed = 0
        created_links = 0

        for i in range(0, total, batch_size):
            batch = appeals[i:i + batch_size]
            print(f'\nProcessing batch {i} - {i + batch_size}')

            for appeal in batch:
                try:
                    phone = cls.normalize(appeal.phone)

                    if len(phone) < 9:
                        continue

                    calls = CallRecord.objects.filter(
                        src__endswith=phone[-9:],
                        audio_downloaded=True,
                    )

                    links = [
                        AppealCallRecord(appeal=appeal, call_record=call)
                        for call in calls
                    ]

                    with transaction.atomic():
                        result = AppealCallRecord.objects.bulk_create(
                            links,
                            ignore_conflicts=True,
                        )

                    created_links += len(result)

                except Exception as e:
                    print(f'Error on appeal {appeal.id}: {e}')

                processed += 1

            print(f'Processed: {processed}/{total}')

        print('\nDONE')
        print(f'Total links created: {created_links}')
        return created_links
