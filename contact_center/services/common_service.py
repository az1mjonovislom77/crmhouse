import logging
from typing import Dict, List, Optional
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import APIException
from common.utils import normalize_phone
from contact_center.models import CallRecord
from contact_center.services.dedub_service import CDRDedupService

logger = logging.getLogger(__name__)


def build_user_phone_map() -> Dict[str, int]:
    User = get_user_model()
    phone_map = {}
    for user_id, phone in User.objects.exclude(phone_number__isnull=True).exclude(
            phone_number='').values_list('id', 'phone_number'):
        digits = normalize_phone(phone)
        if digits:
            phone_map[digits] = user_id
    return phone_map


def match_user_id(phone_map: Dict[str, int], *numbers: Optional[str]) -> Optional[int]:
    for number in numbers:
        user_id = phone_map.get(normalize_phone(number))
        if user_id:
            return user_id
    return None


class ExternalAPIService:
    AUTH_ENDPOINT = '/authenticate'
    CDR_ENDPOINT = '/cdr'
    TIMEOUT = 30

    @classmethod
    def _base_url(cls):
        return settings.PBX_BASE_URL or 'https://sip1.createsoft.uz/pbxapi'

    @classmethod
    def get_access_token(cls):
        url = cls._base_url() + cls.AUTH_ENDPOINT
        data = {
            'user': settings.SIP_API_USER,
            'password': settings.SIP_API_PASSWORD,
        }
        response = requests.post(url, data=data, timeout=cls.TIMEOUT, verify=settings.PBX_VERIFY_SSL)
        if response.status_code != 200:
            raise APIException(f'Token olishda xato: {response.text}')
        return response.json().get('access_token')

    @classmethod
    def fetch_cdr_data(cls, params: dict):
        token = cls.get_access_token()
        url = cls._base_url() + cls.CDR_ENDPOINT
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(url, headers=headers, params=params, timeout=cls.TIMEOUT,
                                verify=settings.PBX_VERIFY_SSL)
        if response.status_code != 200:
            raise APIException(f'CDR olishda xato: {response.text}')
        try:
            payload = response.json()
        except ValueError:
            raise APIException('CDR olishda xato: javob JSON emas')
        if payload.get('status') != 'success':
            raise APIException(f'CDR olishda xato: {response.text}')
        return payload.get('results', [])


class CDRService:

    @staticmethod
    def fetch_and_save_cdr(params: Dict[str, str]) -> int:
        data: List[Dict] = ExternalAPIService.fetch_cdr_data(params)

        phone_map = build_user_phone_map()
        records_to_create = []
        records_map = []
        seen_sessions = set()

        for item in data:
            try:
                if CDRDedupService.should_skip(item, seen_sessions):
                    continue

                calldate = parse_datetime(item['calldate'])
                if calldate is None:
                    logger.warning("CDR yozuvi o'tkazib yuborildi: calldate yaroqsiz (%r)", item.get('calldate'))
                    continue

                record = CallRecord(
                    calldate=calldate,
                    src=item.get('src'),
                    dst=item.get('dst'),
                    user_id=match_user_id(phone_map, item.get('src'), item.get('dst')),
                    uniqueid=item['uniqueid'],
                    disposition=item.get('disposition'),
                    duration=int(item.get('duration') or 0),
                    billsec=int(item.get('billsec') or 0),
                    recordingfile=item.get('recordingfile'),
                )
            except (KeyError, TypeError, ValueError) as e:
                logger.warning("CDR yozuvi o'tkazib yuborildi: %s | %r", e, item)
                continue
            records_to_create.append(record)
            records_map.append((item['uniqueid'], item.get('recordingfile')))

        CallRecord.objects.bulk_create(records_to_create, ignore_conflicts=True, batch_size=500)

        from contact_center.tasks import download_recording_task

        new_records = CallRecord.objects.filter(
            uniqueid__in=[uid for uid, _ in records_map], audio_downloaded=False, recordingfile__isnull=False,
        ).exclude(recordingfile='')
        for record in new_records:
            download_recording_task.delay(record.id)

        return len(records_to_create)
