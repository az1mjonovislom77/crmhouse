from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from leads.models import Lead, LeadEvent, LeadNotification, BOARD_STATUSES
from leads.services.lead_service import LeadService
from user.models import User


def make_user(**kwargs):
    defaults = {'username': 'lead_user', 'full_name': 'Lead User', 'role': User.UserRoles.SELLER}
    defaults.update(kwargs)
    u = User(**defaults)
    u.set_password('pass123')
    u.save()
    return u


def make_lead(**kwargs):
    defaults = {
        'full_name': 'Test Lead',
        'phone': '+998901234567',
        'board': Lead.BOARD_SALES,
        'status': 'yangi_murojaat',
        'sub_status': 'murojaat_qildi',
        'source': 'Instagram',
        'score': 0,
    }
    defaults.update(kwargs)
    return Lead.objects.create(**defaults)


class LeadModelTest(TestCase):
    def test_create_lead(self):
        lead = make_lead()
        self.assertEqual(lead.full_name, 'Test Lead')
        self.assertEqual(lead.board, Lead.BOARD_SALES)

    def test_str_representation(self):
        lead = make_lead()
        self.assertIn('Test Lead', str(lead))
        self.assertIn('sales', str(lead))

    def test_default_score_is_zero(self):
        lead = make_lead()
        self.assertEqual(lead.score, 0)

    def test_default_subsidiya_is_false(self):
        lead = make_lead()
        self.assertFalse(lead.subsidiya)

    def test_ordering_by_created_at_desc(self):
        lead1 = make_lead(full_name='First', phone='111')
        lead2 = make_lead(full_name='Second', phone='222')
        leads = list(Lead.objects.filter(id__in=[lead1.id, lead2.id]))
        self.assertEqual(leads[0].id, lead2.id)


class LeadEventModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.lead = make_lead()

    def test_create_event(self):
        event = LeadEvent.objects.create(
            lead=self.lead, type=LeadEvent.TYPE_COMMENT, text='Test comment', by=self.user)
        self.assertEqual(event.type, LeadEvent.TYPE_COMMENT)
        self.assertEqual(event.lead, self.lead)

    def test_str_representation(self):
        event = LeadEvent.objects.create(
            lead=self.lead, type=LeadEvent.TYPE_CREATED, by=self.user)
        self.assertIn('created', str(event))


class LeadServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_create_lead_sets_first_status(self):
        lead = LeadService.create_lead({
            'full_name': 'New Lead',
            'phone': '+998901111111',
            'board': Lead.BOARD_SALES,
            'source': 'Telegram',
        }, self.user)
        self.assertEqual(lead.status, 'yangi_murojaat')
        self.assertEqual(lead.sub_status, 'murojaat_qildi')

    def test_create_lead_cold_board(self):
        lead = LeadService.create_lead({
            'full_name': 'Cold Lead',
            'phone': '+998902222222',
            'board': Lead.BOARD_COLD,
            'source': 'Boshqa',
        }, self.user)
        self.assertEqual(lead.status, 'yangi')
        self.assertEqual(lead.board, Lead.BOARD_COLD)

    def test_create_lead_creates_created_event(self):
        lead = LeadService.create_lead({
            'full_name': 'Event Lead',
            'phone': '+998903333333',
            'board': Lead.BOARD_SALES,
            'source': 'Instagram',
        }, self.user)
        self.assertTrue(lead.events.filter(type=LeadEvent.TYPE_CREATED).exists())

    def test_create_lead_with_meeting_creates_meeting_event(self):
        meeting_time = timezone.now()
        lead = LeadService.create_lead({
            'full_name': 'Meeting Lead',
            'phone': '+998904444444',
            'board': Lead.BOARD_SALES,
            'source': 'Instagram',
            'meeting_at': meeting_time,
            'meeting_type': 'Ofisda',
        }, self.user)
        self.assertTrue(lead.events.filter(type=LeadEvent.TYPE_MEETING).exists())

    def test_create_lead_computes_score(self):
        lead = LeadService.create_lead({
            'full_name': 'Scored Lead',
            'phone': '+998905555555',
            'board': Lead.BOARD_SALES,
            'source': 'Tavsiya',
        }, self.user)
        self.assertGreater(lead.score, 0)

    def test_create_lead_sets_owner(self):
        lead = LeadService.create_lead({
            'full_name': 'Owner Lead',
            'phone': '+998906666666',
            'board': Lead.BOARD_SALES,
            'source': 'Instagram',
        }, self.user)
        self.assertEqual(lead.owner, self.user)


class LeadServiceUpdateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.lead = make_lead(owner=self.user)

    def test_update_status_creates_event(self):
        LeadService.update_lead(self.lead, {'status': 'uchrashuv'}, self.user)
        self.assertTrue(
            LeadEvent.objects.filter(lead=self.lead, type=LeadEvent.TYPE_STATUS,
                                     to_value='uchrashuv').exists()
        )

    def test_update_invalid_status_raises(self):
        with self.assertRaises(ValidationError):
            LeadService.update_lead(self.lead, {'status': 'noto_gri_status'}, self.user)

    def test_add_comment_creates_event(self):
        LeadService.update_lead(self.lead, {'comment': 'Mijoz qiziqdi'}, self.user)
        self.assertTrue(
            LeadEvent.objects.filter(lead=self.lead, type=LeadEvent.TYPE_COMMENT,
                                     text='Mijoz qiziqdi').exists()
        )

    def test_transfer_creates_event(self):
        new_owner = make_user(username='new_owner_user')
        LeadService.update_lead(self.lead, {'owner': new_owner}, self.user)
        self.assertTrue(
            LeadEvent.objects.filter(lead=self.lead, type=LeadEvent.TYPE_TRANSFER).exists()
        )
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.owner, new_owner)

    def test_update_subsidiya_creates_event(self):
        LeadService.update_lead(self.lead, {'subsidiya': True}, self.user)
        self.assertTrue(
            LeadEvent.objects.filter(lead=self.lead, type=LeadEvent.TYPE_SUBSIDIYA).exists()
        )

    def test_set_meeting_auto_moves_to_uchrashuv(self):
        LeadService.update_lead(self.lead, {
            'meeting_at': timezone.now(),
            'meeting_type': 'Showroomda',
        }, self.user)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, 'uchrashuv')


class LeadViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username='lead_api')
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse('leads-list')

    def test_list_returns_200(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_lead(self):
        resp = self.client.post(self.list_url, {
            'full_name': 'API Lead',
            'phone': '+998901234000',
            'board': Lead.BOARD_SALES,
            'source': 'Instagram',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Lead.objects.filter(full_name='API Lead').exists())

    def test_create_lead_sets_correct_status(self):
        resp = self.client.post(self.list_url, {
            'full_name': 'Status Lead',
            'phone': '+998901234001',
            'board': Lead.BOARD_SALES,
            'source': 'Instagram',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        lead = Lead.objects.get(full_name='Status Lead')
        self.assertEqual(lead.status, 'yangi_murojaat')

    def test_retrieve_lead(self):
        lead = make_lead()
        url = reverse('leads-detail', args=[lead.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['id'], lead.id)

    def test_update_lead_status(self):
        lead = make_lead(owner=self.user)
        url = reverse('leads-detail', args=[lead.id])
        resp = self.client.put(url, {'status': 'uchrashuv'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        lead.refresh_from_db()
        self.assertEqual(lead.status, 'uchrashuv')

    def test_list_with_board_filter(self):
        make_lead(phone='111', board=Lead.BOARD_SALES)
        make_lead(phone='222', board=Lead.BOARD_COLD, status='yangi', sub_status='yangi')
        resp = self.client.get(self.list_url, {'board': Lead.BOARD_COLD})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data['data']:
            self.assertEqual(item['board'], Lead.BOARD_COLD)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_lead(self):
        lead = make_lead()
        url = reverse('leads-detail', args=[lead.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lead.objects.filter(id=lead.id).exists())


class LeadNotificationViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username='notif_user')
        self.client.force_authenticate(user=self.user)

    def test_list_notifications_returns_200(self):
        resp = self.client.get(reverse('lead-notifications-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_returns_only_todays_notifications(self):
        lead = make_lead()
        LeadNotification.objects.create(
            lead=lead, owner=self.user, meeting_at=timezone.now())
        resp = self.client.get(reverse('lead-notifications-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_does_not_return_other_users_notifications(self):
        other = make_user(username='other_user')
        lead = make_lead()
        LeadNotification.objects.create(lead=lead, owner=other, meeting_at=timezone.now())
        resp = self.client.get(reverse('lead-notifications-list'))
        self.assertEqual(len(resp.data), 0)
