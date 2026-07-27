from unittest.mock import MagicMock, patch

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from common.factories import make_user
from contact_center.models import CallRecord
from contact_center.services.common_service import CDRService
from contact_center.services.dedub_service import CDRDedupService
from organization.models import Organization
from user.models import User


def make_call_record(**kwargs):
    defaults = {
        "calldate": timezone.now(),
        "src": "998901234567",
        "dst": "998711234567",
        "disposition": "ANSWERED",
        "duration": 120,
        "billsec": 115,
        "uniqueid": "test-unique-1",
    }
    defaults.update(kwargs)
    return CallRecord.objects.create(**defaults)


class CallRecordModelTest(TestCase):
    def test_create_and_str(self):
        cr = make_call_record(src="998901111111", disposition="ANSWERED")
        self.assertEqual(str(cr), "998901111111 - ANSWERED")

    def test_audio_url_none_when_no_file(self):
        cr = make_call_record()
        self.assertIsNone(cr.audio_url)

    def test_uniqueid_unique_constraint(self):
        make_call_record(uniqueid="dup-001")
        with self.assertRaises(IntegrityError):
            make_call_record(uniqueid="dup-001")


class CDRDedupServiceTest(TestCase):
    def test_answered_call_not_skipped(self):
        item = {"disposition": "ANSWERED", "recordingfile": "rec.wav"}
        seen = set()
        self.assertFalse(CDRDedupService.should_skip(item, seen))

    def test_no_answer_without_recording_not_skipped(self):
        item = {"disposition": "NO ANSWER", "recordingfile": None}
        seen = set()
        self.assertFalse(CDRDedupService.should_skip(item, seen))

    def test_no_answer_first_occurrence_not_skipped(self):
        item = {"disposition": "NO ANSWER", "recordingfile": "session.wav"}
        seen = set()
        self.assertFalse(CDRDedupService.should_skip(item, seen))
        self.assertIn("session.wav", seen)

    def test_no_answer_duplicate_is_skipped(self):
        item = {"disposition": "NO ANSWER", "recordingfile": "session.wav"}
        seen = {"session.wav"}
        self.assertTrue(CDRDedupService.should_skip(item, seen))


class CDRServiceTest(TestCase):
    @patch("contact_center.tasks.download_recording_task")
    @patch("contact_center.services.common_service.ExternalAPIService.fetch_cdr_data")
    def test_fetch_and_save_creates_records(self, mock_fetch, mock_task):
        mock_fetch.return_value = [
            {
                "calldate": "2024-01-01 10:00:00",
                "src": "998901234567",
                "uniqueid": "svc-test-1",
                "disposition": "ANSWERED",
                "duration": "60",
                "billsec": "55",
                "recordingfile": None,
            }
        ]
        mock_task.delay = MagicMock()

        count = CDRService.fetch_and_save_cdr({"startdate": "2024-01-01", "enddate": "2024-01-07"})

        self.assertEqual(count, 1)
        self.assertTrue(CallRecord.objects.filter(uniqueid="svc-test-1").exists())

    @patch("contact_center.tasks.download_recording_task")
    @patch("contact_center.services.common_service.ExternalAPIService.fetch_cdr_data")
    def test_duplicate_uniqueid_ignored(self, mock_fetch, mock_task):
        make_call_record(uniqueid="dup-svc-1")
        mock_fetch.return_value = [
            {
                "calldate": "2024-01-01 10:00:00",
                "src": "998901234567",
                "uniqueid": "dup-svc-1",
                "disposition": "ANSWERED",
                "duration": "60",
                "billsec": "55",
                "recordingfile": None,
            }
        ]
        mock_task.delay = MagicMock()

        CDRService.fetch_and_save_cdr({})
        self.assertEqual(CallRecord.objects.filter(uniqueid="dup-svc-1").count(), 1)


class CDRListViewTest(APITestCase):
    def setUp(self):
        self.user = make_user(role=User.UserRoles.ADMIN)
        self.client.force_authenticate(user=self.user)

    def test_empty_db_triggers_sync_and_returns_200(self):
        with patch("contact_center.views.cdr_view.sync_cdr_data") as mock_sync:
            mock_sync.delay = MagicMock()
            resp = self.client.get("/contact-center/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)

    def test_list_returns_records(self):
        make_call_record(uniqueid="view-test-1")
        resp = self.client.get("/contact-center/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data["count"], 1)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get("/contact-center/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_by_src(self):
        make_call_record(src="998911111111", uniqueid="search-src-1")
        make_call_record(src="998922222222", uniqueid="search-src-2")
        resp = self.client.get("/contact-center/", {"search": "998911111111"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_filter_by_disposition(self):
        make_call_record(disposition="ANSWERED", uniqueid="filt-ans-1")
        make_call_record(disposition="NO ANSWER", uniqueid="filt-no-1")
        resp = self.client.get("/contact-center/", {"disposition": "ANSWERED"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)


class CallRecordOrgScopingTest(APITestCase):
    def setUp(self):
        self.org_a = Organization.objects.create(name="Org A")
        self.org_b = Organization.objects.create(name="Org B")
        self.user_a = make_user(username="seller_a", is_staff=False, organization=self.org_a)
        self.user_b = make_user(username="seller_b", is_staff=False, organization=self.org_b)
        self.record_a = make_call_record(uniqueid="scope-a-1", user=self.user_a, recordingfile="a.wav")
        self.record_b = make_call_record(uniqueid="scope-b-1", user=self.user_b, recordingfile="b.wav")
        self.record_unmatched = make_call_record(uniqueid="scope-none-1")

    def test_list_hides_other_org_records(self):
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get("/contact-center/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        uniqueids = {r["uniqueid"] for r in resp.data["results"]}
        self.assertIn("scope-a-1", uniqueids)
        self.assertIn("scope-none-1", uniqueids)
        self.assertNotIn("scope-b-1", uniqueids)

    def test_staff_sees_all_records(self):
        staff = make_user(username="staff_user", is_staff=True)
        self.client.force_authenticate(user=staff)
        resp = self.client.get("/contact-center/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 3)

    def test_user_without_org_sees_nothing(self):
        orgless = make_user(username="orgless_user", is_staff=False)
        self.client.force_authenticate(user=orgless)
        with patch("contact_center.views.cdr_view.sync_cdr_data") as mock_sync:
            mock_sync.delay = MagicMock()
            resp = self.client.get("/contact-center/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)

    def test_recording_download_other_org_returns_404(self):
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get(f"/contact-center/download-recording/{self.record_b.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_recording_download_own_org_allowed(self):
        self.client.force_authenticate(user=self.user_a)
        with patch("contact_center.views.recording_view.IssabelService") as mock_service:
            upstream = MagicMock()
            upstream.iter_content.return_value = iter([b"audio"])
            mock_service.return_value.stream_recording.return_value = upstream
            resp = self.client.get(f"/contact-center/download-recording/{self.record_a.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
