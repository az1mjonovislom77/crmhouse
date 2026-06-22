from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from booking.models import Booking, Company
from client.models import Client
from client.selectors.client_selectors import get_client_queryset
from home.models import Home, HomeStatusHistory
from user.models import User


def make_user(**kwargs):
    password = kwargs.pop("password", "pass123")
    defaults = {"username": "cl_user", "full_name": "CL User", "role": User.UserRoles.SELLER}
    defaults.update(kwargs)
    u = User(**defaults)
    u.set_password(password)
    u.save()
    return u


def make_client(**kwargs):
    defaults = {
        "full_name": "Test Client",
        "phone_number": "+998901234567",
        "passport": "AA123456",
        "address": "Toshkent",
    }
    defaults.update(kwargs)
    return Client.objects.create(**defaults)


def make_home(**kwargs):
    defaults = {"home_number": 1, "home_status": Home.HomeStatus.AVAILABLE, "price_per_sqm": 0, "area": 0}
    defaults.update(kwargs)
    return Home.objects.create(**defaults)


def make_company(**kwargs):
    defaults = {"name": "Co", "address": "Addr", "phone": "+998"}
    defaults.update(kwargs)
    return Company.objects.create(**defaults)


class ClientModelTest(TestCase):
    def test_create_client(self):
        client = make_client(full_name="Alisher", phone_number="+998901111111")
        self.assertEqual(client.full_name, "Alisher")
        self.assertIsNotNone(client.pk)

    def test_str_returns_full_name(self):
        client = make_client(full_name="Bobur Karimov")
        self.assertEqual(str(client), "Bobur Karimov")

    def test_all_fields_saved(self):
        client = make_client(
            full_name="Full Name",
            phone_number="+998909876543",
            passport="BB654321",
            address="Samarkand",
        )
        client.refresh_from_db()
        self.assertEqual(client.passport, "BB654321")
        self.assertEqual(client.address, "Samarkand")


class ClientSelectorTest(TestCase):
    def setUp(self):
        self.client_obj = make_client()
        self.home = make_home()
        self.company = make_company()
        self.booking = Booking.objects.create(
            home=self.home, client=self.client_obj, company=self.company, cash_payment=0
        )
        HomeStatusHistory.objects.create(
            home=self.home,
            client=self.client_obj,
            from_status=Home.HomeStatus.AVAILABLE,
            to_status=Home.HomeStatus.RESERVED,
        )

    def test_returns_clients(self):
        qs = get_client_queryset()
        self.assertIn(self.client_obj, qs)

    def test_bookings_prefetched(self):
        qs = get_client_queryset()
        client = qs.get(pk=self.client_obj.pk)
        with self.assertNumQueries(0):
            list(client.bookings.all())

    def test_status_history_prefetched(self):
        qs = get_client_queryset()
        client = qs.get(pk=self.client_obj.pk)
        with self.assertNumQueries(0):
            list(client.status_history.all())

    def test_returns_all_clients(self):
        make_client(phone_number="+998911111111")
        make_client(phone_number="+998922222222")
        qs = get_client_queryset()
        self.assertGreaterEqual(qs.count(), 3)


class ClientViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="cl_api")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("client-list")

    def test_list_clients_authenticated(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_client(self):
        data = {
            "full_name": "New Client",
            "phone_number": "+998901234599",
            "passport": "CC999999",
            "address": "Namangan",
        }
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Client.objects.filter(full_name="New Client").exists())

    def test_retrieve_client(self):
        client_obj = make_client(full_name="Retrieve Me")
        url = reverse("client-detail", args=[client_obj.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], client_obj.id)

    def test_update_client(self):
        client_obj = make_client(full_name="Old Name")
        url = reverse("client-detail", args=[client_obj.id])
        data = {
            "full_name": "New Name",
            "phone_number": "+998901234567",
            "passport": "AA123456",
            "address": "Toshkent",
        }
        resp = self.client.put(url, data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        client_obj.refresh_from_db()
        self.assertEqual(client_obj.full_name, "New Name")

    def test_delete_client(self):
        client_obj = make_client(phone_number="+998901111222")
        url = reverse("client-detail", args=[client_obj.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Client.objects.filter(id=client_obj.id).exists())

    def test_list_contains_created_client(self):
        client_obj = make_client(full_name="Listed Client", phone_number="+998903333333")
        resp = self.client.get(self.url)
        ids = [item["id"] for item in resp.data["data"]]
        self.assertIn(client_obj.id, ids)

    def test_pagination_returns_data_key(self):
        resp = self.client.get(self.url)
        self.assertIn("data", resp.data)
        self.assertIn("total", resp.data)
