from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from contact_center.models import CallRecord
from contact_center.services.common_service import CDRService
from contact_center.services.dedub_service import CDRDedupService
from user.models import User


def make_user(**kwargs):
    defaults = {'username': 'cc_user', 'full_name': 'CC User', 'role': User.UserRoles.ADMIN}
    defaults.update(kwargs)
    u = User(**defaults)
    u.set_password('pass123')
    u.save()
    return u


def make_call_record(**kwargs):
    defaults = {
        'calldate': timezone.now(),
        'src': '998901234567',
        'dst': '998711234567',
        'disposition': 'ANSWERED',
        'duration': 120,
        'billsec': 115,
        'uniqueid': 'test-unique-1',
    }
    defaults.update(kwargs)
    return CallRecord.objects.create(**defaults)


class CallRecordModelTest(TestCase):
    def test_create_and_str(self):
        cr = make_call_record(src='998901111111', disposition='ANSWERED')
        self.assertEqual(str(cr), '998901111111 - ANSWERED')

    def test_audio_url_none_when_no_file(self):
        cr = make_call_record()
        self.assertIsNone(cr.audio_url)

    def test_audio_downloaded_default_false(self):
        cr = make_call_record()
        self.assertFalse(cr.audio_downloaded)

    def test_uniqueid_unique_constraint(self):
        make_call_record(uniqueid='dup-001')
        with self.assertRaises(Exception):
            make_call_record(uniqueid='dup-001')

    def test_timestamps_set_on_create(self):
        cr = make_call_record(uniqueid='ts-test-1')
        self.assertIsNotNone(cr.created_at)
        self.assertIsNotNone(cr.updated_at)


class CDRDedupServiceTest(TestCase):
    def test_answered_call_not_skipped(self):
        item = {'disposition': 'ANSWERED', 'recordingfile': 'rec.wav'}
        seen = set()
        self.assertFalse(CDRDedupService.should_skip(item, seen))

    def test_no_answer_without_recording_not_skipped(self):
        item = {'disposition': 'NO ANSWER', 'recordingfile': None}
        seen = set()
        self.assertFalse(CDRDedupService.should_skip(item, seen))

    def test_no_answer_first_occurrence_not_skipped(self):
        item = {'disposition': 'NO ANSWER', 'recordingfile': 'session.wav'}
        seen = set()
        self.assertFalse(CDRDedupService.should_skip(item, seen))
        self.assertIn('session.wav', seen)

    def test_no_answer_duplicate_is_skipped(self):
        item = {'disposition': 'NO ANSWER', 'recordingfile': 'session.wav'}
        seen = {'session.wav'}
        self.assertTrue(CDRDedupService.should_skip(item, seen))


class CDRServiceTest(TestCase):
    @patch('contact_center.tasks.download_recording_task')
    @patch('contact_center.services.common_service.ExternalAPIService.fetch_cdr_data')
    def test_fetch_and_save_creates_records(self, mock_fetch, mock_task):
        mock_fetch.return_value = [
            {
                'calldate': '2024-01-01 10:00:00',
                'src': '998901234567',
                'uniqueid': 'svc-test-1',
                'disposition': 'ANSWERED',
                'duration': '60',
                'billsec': '55',
                'recordingfile': None,
            }
        ]
        mock_task.delay = MagicMock()

        count = CDRService.fetch_and_save_cdr({'startdate': '2024-01-01', 'enddate': '2024-01-07'})

        self.assertEqual(count, 1)
        self.assertTrue(CallRecord.objects.filter(uniqueid='svc-test-1').exists())

    @patch('contact_center.tasks.download_recording_task')
    @patch('contact_center.services.common_service.ExternalAPIService.fetch_cdr_data')
    def test_duplicate_uniqueid_ignored(self, mock_fetch, mock_task):
        make_call_record(uniqueid='dup-svc-1')
        mock_fetch.return_value = [
            {
                'calldate': '2024-01-01 10:00:00',
                'src': '998901234567',
                'uniqueid': 'dup-svc-1',
                'disposition': 'ANSWERED',
                'duration': '60',
                'billsec': '55',
                'recordingfile': None,
            }
        ]
        mock_task.delay = MagicMock()

        CDRService.fetch_and_save_cdr({})
        self.assertEqual(CallRecord.objects.filter(uniqueid='dup-svc-1').count(), 1)


class CDRListViewTest(APITestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_authenticate(user=self.user)

    def test_empty_db_triggers_sync_and_returns_200(self):
        with patch('contact_center.views.cdr_view.sync_cdr_data') as mock_sync:
            mock_sync.delay = MagicMock()
            resp = self.client.get('/contact-center/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 0)

    def test_list_returns_records(self):
        make_call_record(uniqueid='view-test-1')
        resp = self.client.get('/contact-center/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data['count'], 1)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get('/contact-center/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_by_src(self):
        make_call_record(src='998911111111', uniqueid='search-src-1')
        make_call_record(src='998922222222', uniqueid='search-src-2')
        resp = self.client.get('/contact-center/', {'search': '998911111111'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)

    def test_filter_by_disposition(self):
        make_call_record(disposition='ANSWERED', uniqueid='filt-ans-1')
        make_call_record(disposition='NO ANSWER', uniqueid='filt-no-1')
        resp = self.client.get('/contact-center/', {'disposition': 'ANSWERED'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)
