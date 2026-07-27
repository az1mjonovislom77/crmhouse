from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from common.factories import make_user
from leads.models import STATUS_TOPSHIRIQLAR, Lead, LeadEvent, LeadNotification
from leads.services.lead_service import LeadService
from leads.services.notification_service import MeetingNotificationService
from organization.models import Organization
from user.models import User


def make_lead(**kwargs):
    defaults = {
        "full_name": "Test Lead",
        "phone": "+998901234567",
        "board": Lead.BOARD_SALES,
        "status": "yangi_murojaat",
        "sub_status": "murojaat_qildi",
        "source": "Instagram",
        "score": 0,
    }
    defaults.update(kwargs)
    if defaults.get("owner") and not defaults.get("assignee"):
        defaults["assignee"] = defaults["owner"]
    return Lead.objects.create(**defaults)


class LeadModelTest(TestCase):
    def test_str_representation(self):
        lead = make_lead()
        self.assertIn("Test Lead", str(lead))
        self.assertIn("sales", str(lead))

    def test_ordering_by_created_at_desc(self):
        lead1 = make_lead(full_name="First", phone="111")
        lead2 = make_lead(full_name="Second", phone="222")
        leads = list(Lead.objects.filter(id__in=[lead1.id, lead2.id]))
        self.assertEqual(leads[0].id, lead2.id)


class LeadEventModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.lead = make_lead()

    def test_str_representation(self):
        event = LeadEvent.objects.create(lead=self.lead, type=LeadEvent.TYPE_CREATED, by=self.user)
        self.assertIn("created", str(event))


class LeadServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_create_lead_sets_first_status(self):
        lead = LeadService.create_lead(
            {
                "full_name": "New Lead",
                "phone": "+998901111111",
                "board": Lead.BOARD_SALES,
                "source": "Telegram",
            },
            self.user,
        )
        self.assertEqual(lead.status, "yangi_murojaat")
        self.assertEqual(lead.sub_status, "murojaat_qildi")

    def test_create_lead_cold_board(self):
        lead = LeadService.create_lead(
            {
                "full_name": "Cold Lead",
                "phone": "+998902222222",
                "board": Lead.BOARD_COLD,
                "source": "Boshqa",
            },
            self.user,
        )
        self.assertEqual(lead.status, "yangi")
        self.assertEqual(lead.board, Lead.BOARD_COLD)

    def test_create_lead_creates_created_event(self):
        lead = LeadService.create_lead(
            {
                "full_name": "Event Lead",
                "phone": "+998903333333",
                "board": Lead.BOARD_SALES,
                "source": "Instagram",
            },
            self.user,
        )
        self.assertTrue(lead.events.filter(type=LeadEvent.TYPE_CREATED).exists())

    def test_create_lead_with_meeting_creates_meeting_event(self):
        meeting_time = timezone.now()
        lead = LeadService.create_lead(
            {
                "full_name": "Meeting Lead",
                "phone": "+998904444444",
                "board": Lead.BOARD_SALES,
                "source": "Instagram",
                "meeting_at": meeting_time,
                "meeting_type": "Ofisda",
            },
            self.user,
        )
        self.assertTrue(lead.events.filter(type=LeadEvent.TYPE_MEETING).exists())

    def test_create_lead_computes_score(self):
        lead = LeadService.create_lead(
            {
                "full_name": "Scored Lead",
                "phone": "+998905555555",
                "board": Lead.BOARD_SALES,
                "source": "Tavsiya",
            },
            self.user,
        )
        self.assertGreater(lead.score, 0)

    def test_create_lead_sets_owner(self):
        lead = LeadService.create_lead(
            {
                "full_name": "Owner Lead",
                "phone": "+998906666666",
                "board": Lead.BOARD_SALES,
                "source": "Instagram",
            },
            self.user,
        )
        self.assertEqual(lead.owner, self.user)
        self.assertEqual(lead.assignee, self.user)


class LeadServiceUpdateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.lead = make_lead(owner=self.user)

    def test_update_status_creates_event(self):
        LeadService.update_lead(self.lead, {"status": "uchrashuv"}, self.user)
        self.assertTrue(
            LeadEvent.objects.filter(lead=self.lead, type=LeadEvent.TYPE_STATUS, to_value="uchrashuv").exists()
        )

    def test_update_invalid_status_raises(self):
        with self.assertRaises(ValidationError):
            LeadService.update_lead(self.lead, {"status": "noto_gri_status"}, self.user)

    def test_add_comment_creates_event(self):
        LeadService.update_lead(self.lead, {"comment": "Mijoz qiziqdi"}, self.user)
        self.assertTrue(
            LeadEvent.objects.filter(lead=self.lead, type=LeadEvent.TYPE_COMMENT, text="Mijoz qiziqdi").exists()
        )

    def test_transfer_creates_event(self):
        new_assignee = make_user(username="new_assignee_user")
        LeadService.update_lead(self.lead, {"assignee": new_assignee}, self.user)
        self.assertTrue(LeadEvent.objects.filter(lead=self.lead, type=LeadEvent.TYPE_TRANSFER).exists())
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.owner, self.user)
        self.assertEqual(self.lead.assignee, new_assignee)

    def test_transfer_moves_to_topshiriqlar_for_assignee(self):
        new_assignee = make_user(username="delegated_user")
        LeadService.update_lead(self.lead, {"assignee": new_assignee}, self.user)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, STATUS_TOPSHIRIQLAR)
        self.assertEqual(self.lead.sub_status, "yangi_topshiriq")

    def test_transfer_back_to_owner_leaves_topshiriqlar(self):
        assignee = make_user(username="temp_assignee")
        LeadService.update_lead(self.lead, {"assignee": assignee}, self.user)
        LeadService.update_lead(self.lead, {"assignee": self.user}, self.user)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, "yangi_murojaat")
        self.assertEqual(self.lead.assignee, self.user)

    def test_assignee_status_change_visible_in_history(self):
        assignee = make_user(username="worker_user")
        LeadService.update_lead(self.lead, {"assignee": assignee}, self.user)
        LeadService.update_lead(self.lead, {"status": "uchrashuv"}, assignee)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.owner, self.user)
        self.assertEqual(self.lead.status, "uchrashuv")
        status_event = LeadEvent.objects.filter(
            lead=self.lead,
            type=LeadEvent.TYPE_STATUS,
            to_value="uchrashuv",
        ).latest("at")
        self.assertEqual(status_event.by, assignee)

    def test_update_subsidiya_creates_event(self):
        LeadService.update_lead(self.lead, {"subsidiya": True}, self.user)
        self.assertTrue(LeadEvent.objects.filter(lead=self.lead, type=LeadEvent.TYPE_SUBSIDIYA).exists())

    def test_set_meeting_auto_moves_to_uchrashuv(self):
        LeadService.update_lead(
            self.lead,
            {
                "meeting_at": timezone.now(),
                "meeting_type": "Showroomda",
            },
            self.user,
        )
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, "uchrashuv")


class LeadViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="lead_api")
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse("leads-list")

    def test_list_returns_200(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_lead(self):
        resp = self.client.post(
            self.list_url,
            {
                "full_name": "API Lead",
                "phone": "+998901234000",
                "board": Lead.BOARD_SALES,
                "source": "Instagram",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Lead.objects.filter(full_name="API Lead").exists())

    def test_create_lead_sets_correct_status(self):
        resp = self.client.post(
            self.list_url,
            {
                "full_name": "Status Lead",
                "phone": "+998901234001",
                "board": Lead.BOARD_SALES,
                "source": "Instagram",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        lead = Lead.objects.get(full_name="Status Lead")
        self.assertEqual(lead.status, "yangi_murojaat")

    def test_retrieve_lead(self):
        lead = make_lead()
        url = reverse("leads-detail", args=[lead.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], lead.id)

    def test_update_lead_status(self):
        lead = make_lead(owner=self.user)
        url = reverse("leads-detail", args=[lead.id])
        resp = self.client.put(url, {"status": "uchrashuv"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        lead.refresh_from_db()
        self.assertEqual(lead.status, "uchrashuv")

    def test_update_lead_assignee_keeps_owner(self):
        admin = make_user(username="lead_admin", role=User.UserRoles.ADMIN)
        self.client.force_authenticate(user=admin)
        lead = make_lead(owner=admin)
        assignee = make_user(username="api_assignee")
        url = reverse("leads-detail", args=[lead.id])
        resp = self.client.put(url, {"assignee": assignee.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        lead.refresh_from_db()
        self.assertEqual(lead.owner, admin)
        self.assertEqual(lead.assignee, assignee)
        self.assertEqual(resp.data["owner_id"], admin.id)
        self.assertEqual(resp.data["assignee_id"], assignee.id)

    def test_seller_cannot_assign_lead(self):
        seller = make_user(username="lead_seller", role=User.UserRoles.SELLER, is_staff=False)
        org = Organization.objects.create(name="Seller Org")
        seller.organization = org
        seller.save(update_fields=["organization"])
        self.client.force_authenticate(user=seller)
        lead = make_lead(owner=seller)
        assignee = make_user(username="blocked_assignee", organization=org)
        url = reverse("leads-detail", args=[lead.id])
        resp = self.client.put(url, {"assignee": assignee.id})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assignee", resp.data)

    def test_list_with_board_filter(self):
        make_lead(phone="111", board=Lead.BOARD_SALES)
        make_lead(phone="222", board=Lead.BOARD_COLD, status="yangi", sub_status="yangi")
        resp = self.client.get(self.list_url, {"board": Lead.BOARD_COLD})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data["data"]:
            self.assertEqual(item["board"], Lead.BOARD_COLD)

    def test_list_with_assignee_filter(self):
        assignee = make_user(username="assigned_user")
        other = make_user(username="other_assigned_user")
        lead = make_lead(phone="333", owner=self.user, assignee=assignee)
        make_lead(phone="444", owner=self.user, assignee=other)
        resp = self.client.get(self.list_url, {"assignee": assignee.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in resp.data["data"]], [lead.id])

    def test_topshiriqlar_list_shows_only_current_assignee_leads(self):
        org = Organization.objects.create(name="Tasks Org")
        owner = make_user(username="task_owner", is_staff=False, organization=org)
        assignee = make_user(username="my_tasks_user", is_staff=False, organization=org)
        other = make_user(username="other_tasks_user", is_staff=False, organization=org)
        my_lead = make_lead(
            phone="555",
            owner=owner,
            assignee=assignee,
            status=STATUS_TOPSHIRIQLAR,
            sub_status="yangi_topshiriq",
        )
        make_lead(
            phone="666",
            owner=owner,
            assignee=other,
            status=STATUS_TOPSHIRIQLAR,
            sub_status="yangi_topshiriq",
        )
        self.client.force_authenticate(user=assignee)
        resp = self.client.get(self.list_url, {"status": STATUS_TOPSHIRIQLAR})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in resp.data["data"]], [my_lead.id])
        self.assertEqual(resp.data["counts"]["topshiriqlar"], 1)

    def test_seller_list_shows_only_own_leads(self):
        org = Organization.objects.create(name="Scope Org")
        seller = make_user(username="scope_seller", role=User.UserRoles.SELLER, is_staff=False, organization=org)
        other = make_user(username="scope_other", is_staff=False, organization=org)
        my_lead = make_lead(phone="scope1", owner=seller)
        make_lead(phone="scope2", owner=other)
        self.client.force_authenticate(user=seller)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in resp.data["data"]], [my_lead.id])

    def test_admin_list_shows_all_org_leads(self):
        org = Organization.objects.create(name="Admin Scope Org")
        admin = make_user(username="scope_admin", role=User.UserRoles.ADMIN, organization=org)
        seller = make_user(username="scope_seller2", is_staff=False, organization=org)
        lead1 = make_lead(phone="adm1", owner=admin)
        lead2 = make_lead(phone="adm2", owner=seller)
        self.client.force_authenticate(user=admin)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual({item["id"] for item in resp.data["data"]}, {lead1.id, lead2.id})

    def test_seller_cannot_retrieve_other_lead(self):
        org = Organization.objects.create(name="Retrieve Scope Org")
        seller = make_user(username="retrieve_seller", role=User.UserRoles.SELLER, is_staff=False, organization=org)
        other = make_user(username="retrieve_other", is_staff=False, organization=org)
        lead = make_lead(phone="ret1", owner=other)
        self.client.force_authenticate(user=seller)
        resp = self.client.get(reverse("leads-detail", args=[lead.id]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_transfer_via_api_sets_topshiriqlar_and_keeps_owner(self):
        admin = make_user(username="transfer_admin", role=User.UserRoles.ADMIN)
        self.client.force_authenticate(user=admin)
        lead = make_lead(owner=admin)
        assignee = make_user(username="api_task_user")
        url = reverse("leads-detail", args=[lead.id])
        resp = self.client.put(url, {"assignee": assignee.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        lead.refresh_from_db()
        self.assertEqual(lead.owner, admin)
        self.assertEqual(lead.assignee, assignee)
        self.assertEqual(lead.status, STATUS_TOPSHIRIQLAR)
        transfer = LeadEvent.objects.filter(lead=lead, type=LeadEvent.TYPE_TRANSFER).latest("at")
        self.assertEqual(transfer.by, admin)
        self.assertEqual(transfer.from_value, admin.full_name)
        self.assertEqual(transfer.to_value, assignee.full_name)

    def test_bulk_assign_multiple_leads(self):
        admin = make_user(username="bulk_admin", role=User.UserRoles.ADMIN)
        self.client.force_authenticate(user=admin)
        assignee = make_user(username="bulk_assignee")
        lead1 = make_lead(phone="777", owner=admin)
        lead2 = make_lead(phone="888", owner=admin)
        url = reverse("leads-bulk-assign")
        resp = self.client.post(
            url,
            {
                "lead_ids": [lead1.id, lead2.id],
                "assignee_to": assignee.id,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["updated"], 2)
        self.assertEqual(set(resp.data["lead_ids"]), {lead1.id, lead2.id})
        self.assertEqual(resp.data["assignee_id"], assignee.id)
        lead1.refresh_from_db()
        lead2.refresh_from_db()
        self.assertEqual(lead1.assignee, assignee)
        self.assertEqual(lead2.assignee, assignee)
        self.assertEqual(lead1.status, STATUS_TOPSHIRIQLAR)
        self.assertEqual(lead2.status, STATUS_TOPSHIRIQLAR)
        self.assertEqual(lead1.owner, admin)
        self.assertEqual(lead2.owner, admin)

    def test_seller_cannot_bulk_assign(self):
        seller = make_user(username="bulk_seller", role=User.UserRoles.SELLER, is_staff=False)
        org = Organization.objects.create(name="Bulk Seller Org")
        seller.organization = org
        seller.save(update_fields=["organization"])
        self.client.force_authenticate(user=seller)
        assignee = make_user(username="bulk_blocked_assignee", organization=org)
        lead = make_lead(phone="bulk_one", owner=seller)
        url = reverse("leads-bulk-assign")
        resp = self.client.post(
            url,
            {
                "lead_ids": [lead.id],
                "assignee_to": assignee.id,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_assign_invalid_lead_id(self):
        admin = make_user(username="bulk_invalid_admin", role=User.UserRoles.ADMIN)
        self.client.force_authenticate(user=admin)
        assignee = make_user(username="bulk_invalid_assignee")
        lead = make_lead(phone="999", owner=admin)
        url = reverse("leads-bulk-assign")
        resp = self.client.post(
            url,
            {
                "lead_ids": [lead.id, 99999],
                "assignee_to": assignee.id,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_last_contacted_range(self):
        make_lead(phone="lc_old", owner=self.user, last_contacted=timezone.make_aware(datetime(2026, 1, 10, 12, 0)))
        mid = make_lead(
            phone="lc_mid", owner=self.user, last_contacted=timezone.make_aware(datetime(2026, 2, 15, 12, 0))
        )
        make_lead(phone="lc_new", owner=self.user, last_contacted=timezone.make_aware(datetime(2026, 3, 20, 12, 0)))
        resp = self.client.get(
            self.list_url,
            {
                "last_contacted_from": "2026-02-01",
                "last_contacted_to": "2026-02-28",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in resp.data["data"]], [mid.id])

    def test_order_by_last_contacted(self):
        lead_old = make_lead(
            phone="ord_old", owner=self.user, last_contacted=timezone.make_aware(datetime(2026, 1, 1, 10, 0))
        )
        lead_new = make_lead(
            phone="ord_new", owner=self.user, last_contacted=timezone.make_aware(datetime(2026, 3, 1, 10, 0))
        )
        resp = self.client.get(self.list_url, {"ordering": "last_contacted"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in resp.data["data"] if item["id"] in (lead_old.id, lead_new.id)]
        self.assertEqual(ids, [lead_old.id, lead_new.id])

        resp = self.client.get(self.list_url, {"ordering": "-last_contacted"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in resp.data["data"] if item["id"] in (lead_old.id, lead_new.id)]
        self.assertEqual(ids, [lead_new.id, lead_old.id])

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_lead(self):
        lead = make_lead()
        url = reverse("leads-detail", args=[lead.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lead.objects.filter(id=lead.id).exists())


class LeadNotificationViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="notif_user")
        self.client.force_authenticate(user=self.user)

    def test_list_notifications_returns_200(self):
        resp = self.client.get(reverse("lead-notifications-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_returns_only_todays_notifications(self):
        lead = make_lead()
        LeadNotification.objects.create(lead=lead, owner=self.user, meeting_at=timezone.now())
        resp = self.client.get(reverse("lead-notifications-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_does_not_return_other_users_notifications(self):
        other = make_user(username="other_user")
        lead = make_lead()
        LeadNotification.objects.create(lead=lead, owner=other, meeting_at=timezone.now())
        resp = self.client.get(reverse("lead-notifications-list"))
        self.assertEqual(len(resp.data), 0)


class MeetingNotificationServiceTest(TestCase):
    def test_notifications_are_created_for_assignee(self):
        owner = make_user(username="meeting_owner")
        assignee = make_user(username="meeting_assignee")
        meeting_at = timezone.now()
        lead = make_lead(owner=owner, assignee=assignee, meeting_at=meeting_at)

        created_ids = MeetingNotificationService.check_and_create()

        self.assertEqual(len(created_ids), 1)
        notification = LeadNotification.objects.get(lead=lead)
        self.assertEqual(notification.owner, assignee)
