from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase
from booking.models import Booking, Company, PaymentTerm
from booking.services.booking import create_booking, delete_booking
from client.models import Client
from home.models import Home, HomeStatusHistory
from user.models import User


def make_user(**kwargs):
    password = kwargs.pop("password", "pass123")
    defaults = {"username": "bk_user", "full_name": "BK User", "role": User.UserRoles.SELLER}
    defaults.update(kwargs)
    u = User(**defaults)
    u.set_password(password)
    u.save()
    return u


def make_home(**kwargs):
    defaults = {
        "home_number": 1,
        "home_status": Home.HomeStatus.AVAILABLE,
        "price_per_sqm": 500,
        "area": 50,
    }
    defaults.update(kwargs)
    return Home.objects.create(**defaults)


def make_client(**kwargs):
    defaults = {
        "full_name": "Test Client",
        "phone_number": "+998901234567",
        "passport": "AA123456",
        "address": "Toshkent",
    }
    defaults.update(kwargs)
    return Client.objects.create(**defaults)


def make_company(**kwargs):
    defaults = {"name": "Test Co", "address": "Addr", "phone": "+998"}
    defaults.update(kwargs)
    return Company.objects.create(**defaults)


def make_payment_term(**kwargs):
    defaults = {"months": 12}
    defaults.update(kwargs)
    return PaymentTerm.objects.create(**defaults)


def make_booking(**kwargs):
    defaults = {
        "home": make_home(),
        "client": make_client(),
        "company": make_company(),
        "cash_payment": 0,
    }
    defaults.update(kwargs)
    return Booking.objects.create(**defaults)


class PaymentTermModelTest(TestCase):
    def test_create_payment_term(self):
        pt = PaymentTerm.objects.create(months=24)
        self.assertEqual(pt.months, 24)

    def test_str(self):
        pt = PaymentTerm.objects.create(months=6)
        self.assertIn("6", str(pt))


class CompanyModelTest(TestCase):
    def test_create_company(self):
        co = make_company(name="My Co")
        self.assertEqual(co.name, "My Co")

    def test_str(self):
        co = make_company(name="Alpha")
        self.assertEqual(str(co), "Alpha")


class BookingModelTest(TestCase):
    def setUp(self):
        self.home = make_home()
        self.client_obj = make_client()
        self.company = make_company()

    def test_create_booking(self):
        booking = Booking.objects.create(
            home=self.home, client=self.client_obj, company=self.company, cash_payment=5000
        )
        self.assertEqual(booking.cash_payment, 5000)
        self.assertEqual(booking.home, self.home)

    def test_booking_str_is_id(self):
        booking = Booking.objects.create(
            home=self.home, client=self.client_obj, company=self.company, cash_payment=0
        )
        self.assertEqual(str(booking), str(booking.id))

    def test_one_home_one_booking_constraint(self):
        Booking.objects.create(home=self.home, client=self.client_obj, company=self.company, cash_payment=0)
        with self.assertRaises(Exception):
            Booking.objects.create(
                home=self.home,
                client=make_client(phone_number="+998911234567"),
                company=self.company,
                cash_payment=0,
            )


class CreateBookingServiceTest(TestCase):
    def setUp(self):
        self.user = make_user(username="bk_svc")
        self.home = make_home()
        self.client_obj = make_client()
        self.company = make_company()

    def test_create_booking_basic(self):
        booking = create_booking(
            data={"home": self.home, "client": self.client_obj, "company": self.company, "cash_payment": 0},
            user=self.user,
        )
        self.assertIsNotNone(booking.pk)
        self.assertEqual(booking.home, self.home)

    def test_create_booking_uses_first_company_when_not_provided(self):
        booking = create_booking(
            data={"home": self.home, "client": self.client_obj, "cash_payment": 0},
            user=self.user,
        )
        self.assertEqual(booking.company, self.company)

    def test_create_booking_no_company_raises(self):
        Company.objects.all().delete()
        with self.assertRaises(ValidationError):
            create_booking(
                data={"home": self.home, "client": self.client_obj, "cash_payment": 0},
                user=self.user,
            )

    def test_create_booking_changes_home_status(self):
        create_booking(
            data={"home": self.home, "client": self.client_obj, "company": self.company, "cash_payment": 0},
            user=self.user,
            home_status=Home.HomeStatus.RESERVED,
        )
        self.home.refresh_from_db()
        self.assertEqual(self.home.home_status, Home.HomeStatus.RESERVED)

    def test_create_booking_creates_status_history(self):
        create_booking(
            data={"home": self.home, "client": self.client_obj, "company": self.company, "cash_payment": 0},
            user=self.user,
            home_status=Home.HomeStatus.SOLD,
        )
        self.assertTrue(HomeStatusHistory.objects.filter(home=self.home).exists())

    def test_create_booking_without_home_status_keeps_status(self):
        original = self.home.home_status
        create_booking(
            data={"home": self.home, "client": self.client_obj, "company": self.company, "cash_payment": 0},
            user=self.user,
        )
        self.home.refresh_from_db()
        self.assertEqual(self.home.home_status, original)

    def test_create_booking_records_changed_by(self):
        create_booking(
            data={"home": self.home, "client": self.client_obj, "company": self.company, "cash_payment": 0},
            user=self.user,
            home_status=Home.HomeStatus.RESERVED,
        )
        history = HomeStatusHistory.objects.get(home=self.home)
        self.assertEqual(history.changed_by, self.user)


class DeleteBookingServiceTest(TestCase):
    def setUp(self):
        self.user = make_user(username="del_svc")
        self.home = make_home(home_status=Home.HomeStatus.SOLD)
        self.client_obj = make_client()
        self.company = make_company()
        self.booking = Booking.objects.create(
            home=self.home, client=self.client_obj, company=self.company, cash_payment=0
        )

    def test_delete_booking_removes_record(self):
        bk_id = self.booking.id
        delete_booking(booking_id=bk_id, user=self.user)
        self.assertFalse(Booking.objects.filter(id=bk_id).exists())

    def test_delete_booking_sets_home_to_available(self):
        delete_booking(booking_id=self.booking.id, user=self.user)
        self.home.refresh_from_db()
        self.assertEqual(self.home.home_status, Home.HomeStatus.AVAILABLE)

    def test_delete_booking_creates_deleted_history(self):
        delete_booking(booking_id=self.booking.id, user=self.user)
        self.assertTrue(
            HomeStatusHistory.objects.filter(home=self.home, to_status="booking_deleted").exists()
        )

    def test_delete_booking_records_user(self):
        delete_booking(booking_id=self.booking.id, user=self.user)
        history = HomeStatusHistory.objects.filter(home=self.home, to_status="booking_deleted").first()
        self.assertEqual(history.changed_by, self.user)


class PaymentTermViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="pt_api")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("payment-term-list")

    def test_list_returns_200(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_payment_term(self):
        resp = self.client.post(self.url, {"months": 24})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PaymentTerm.objects.filter(months=24).exists())

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_payment_term(self):
        pt = PaymentTerm.objects.create(months=6)
        url = reverse("payment-term-detail", args=[pt.id])
        resp = self.client.put(url, {"months": 9})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        pt.refresh_from_db()
        self.assertEqual(pt.months, 9)

    def test_delete_payment_term(self):
        pt = PaymentTerm.objects.create(months=3)
        url = reverse("payment-term-detail", args=[pt.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PaymentTerm.objects.filter(id=pt.id).exists())


class BookingViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="bk_api")
        self.client.force_authenticate(user=self.user)
        self.company = make_company()
        self.home = make_home()
        self.client_obj = make_client()
        self.list_url = reverse("booking-list")

    def test_list_bookings(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_filter_by_home_id(self):
        Booking.objects.create(home=self.home, client=self.client_obj, company=self.company, cash_payment=0)
        other_home = make_home(home_number=99)
        Booking.objects.create(
            home=other_home,
            client=make_client(phone_number="+998991234568"),
            company=self.company,
            cash_payment=0,
        )
        resp = self.client.get(self.list_url, {"home_id": self.home.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_create_booking_via_api(self):
        data = {
            "home": self.home.id,
            "client": self.client_obj.id,
            "company": self.company.id,
            "cash_payment": "1000.00",
            "home_status": Home.HomeStatus.RESERVED,
        }
        resp = self.client.post(self.list_url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Booking.objects.filter(home=self.home).exists())

    def test_delete_booking_via_api(self):
        booking = Booking.objects.create(
            home=self.home, client=self.client_obj, company=self.company, cash_payment=0
        )
        url = reverse("booking-detail", args=[booking.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Booking.objects.filter(id=booking.id).exists())

    def test_retrieve_booking(self):
        booking = Booking.objects.create(
            home=self.home, client=self.client_obj, company=self.company, cash_payment=0
        )
        url = reverse("booking-detail", args=[booking.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], booking.id)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
