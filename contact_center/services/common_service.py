from typing import Dict, List

import requests
from django.conf import settings
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import APIException

from contact_center.models import CallRecord
from contact_center.services.dedub_service import CDRDedupService


class ExternalAPIService:
    BASE_URL = 'https://sip1.createsoft.uz/pbxapi'
    AUTH_ENDPOINT = '/authenticate'
    CDR_ENDPOINT = '/cdr'

    @classmethod
    def get_access_token(cls):
        url = cls.BASE_URL + cls.AUTH_ENDPOINT
        data = {
            'user': settings.SIP_API_USER,
            'password': settings.SIP_API_PASSWORD,
        }
        response = requests.post(url, data=data, verify=False)
        if response.status_code != 200:
            raise APIException(f'Token olishda xato: {response.text}')
        return response.json().get('access_token')

    @classmethod
    def fetch_cdr_data(cls, params: dict):
        token = cls.get_access_token()
        url = cls.BASE_URL + cls.CDR_ENDPOINT
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(url, headers=headers, params=params, verify=False)
        if response.status_code != 200 or response.json().get('status') != 'success':
            raise APIException(f'CDR olishda xato: {response.text}')
        return response.json().get('results', [])


class CDRService:

    @staticmethod
    def fetch_and_save_cdr(params: Dict[str, str]) -> int:
        data: List[Dict] = ExternalAPIService.fetch_cdr_data(params)

        records_to_create = []
        records_map = []
        seen_sessions = set()

        for item in data:
            if CDRDedupService.should_skip(item, seen_sessions):
                continue

            calldate = parse_datetime(item['calldate'])
            record = CallRecord(
                calldate=calldate,
                src=item.get('src'),
                uniqueid=item['uniqueid'],
                disposition=item.get('disposition'),
                duration=int(item.get('duration', 0)),
                billsec=int(item.get('billsec', 0)),
                recordingfile=item.get('recordingfile'),
            )
            records_to_create.append(record)
            records_map.append((item['uniqueid'], item.get('recordingfile')))

        CallRecord.objects.bulk_create(
            records_to_create,
            ignore_conflicts=True,
            batch_size=500,
        )

        from contact_center.tasks import download_recording_task

        new_records = CallRecord.objects.filter(
            uniqueid__in=[uid for uid, _ in records_map],
            audio_downloaded=False,
            recordingfile__isnull=False,
        )
        for record in new_records:
            download_recording_task.delay(record.id)

        return len(records_to_create)
