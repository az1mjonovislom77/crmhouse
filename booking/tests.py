from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase
from booking.models import Booking, Company
from booking.services.booking import create_booking, delete_booking
from client.models import Client
from home.models import Home, HomeStatusHistory
from user.models import User


def make_user(**kwargs):
    password = kwargs.pop("password", "pass123")
    defaults = {"username": "bk_user", "full_name": "BK User", "role": User.UserRoles.SELLER, "is_staff": True}
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


def make_booking(**kwargs):
    defaults = {
        "home": make_home(),
        "client": make_client(),
        "company": make_company(),
    }
    defaults.update(kwargs)
    return Booking.objects.create(**defaults)


class CompanyModelTest(TestCase):
    def test_str(self):
        co = make_company(name="Alpha")
        self.assertEqual(str(co), "Alpha")


class BookingModelTest(TestCase):
    def setUp(self):
        self.home = make_home()
        self.client_obj = make_client()
        self.company = make_company()

    def test_booking_str_is_id(self):
        booking = Booking.objects.create(
            home=self.home, client=self.client_obj, company=self.company        )
        self.assertEqual(str(booking), str(booking.id))

    def test_one_home_one_booking_constraint(self):
        Booking.objects.create(home=self.home, client=self.client_obj, company=self.company)
        with self.assertRaises(Exception):
            Booking.objects.create(
                home=self.home,
                client=make_client(phone_number="+998911234567"),
                company=self.company,            )


class CreateBookingServiceTest(TestCase):
    def setUp(self):
        self.user = make_user(username="bk_svc")
        self.home = make_home()
        self.client_obj = make_client()
        self.company = make_company()

    def test_create_booking_basic(self):
        booking = create_booking(
            data={"home": self.home, "client": self.client_obj, "company": self.company},
            user=self.user
        )
        self.assertIsNotNone(booking.pk)
        self.assertEqual(booking.home, self.home)

    def test_create_booking_uses_first_company_when_not_provided(self):
        booking = create_booking(
            data={"home": self.home, "client": self.client_obj},
            user=self.user,
        )
        self.assertEqual(booking.company, self.company)

    def test_create_booking_no_company_raises(self):
        Company.objects.all().delete()
        with self.assertRaises(ValidationError):
            create_booking(
                data={"home": self.home, "client": self.client_obj},
                user=self.user,
            )

    def test_create_booking_changes_home_status(self):
        create_booking(
            data={"home": self.home, "client": self.client_obj, "company": self.company},
            user=self.user,
            home_status=Home.HomeStatus.RESERVED,
        )
        self.home.refresh_from_db()
        self.assertEqual(self.home.home_status, Home.HomeStatus.RESERVED)

    def test_create_booking_creates_status_history(self):
        create_booking(
            data={"home": self.home, "client": self.client_obj, "company": self.company},
            user=self.user,
            home_status=Home.HomeStatus.SOLD,
        )
        self.assertTrue(HomeStatusHistory.objects.filter(home=self.home).exists())

    def test_create_booking_without_home_status_keeps_status(self):
        original = self.home.home_status
        create_booking(
            data={"home": self.home, "client": self.client_obj, "company": self.company},
            user=self.user,
        )
        self.home.refresh_from_db()
        self.assertEqual(self.home.home_status, original)

    def test_create_booking_records_changed_by(self):
        create_booking(
            data={"home": self.home, "client": self.client_obj, "company": self.company},
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
            home=self.home, client=self.client_obj, company=self.company        )

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
        Booking.objects.create(home=self.home, client=self.client_obj, company=self.company)
        other_home = make_home(home_number=99)
        Booking.objects.create(
            home=other_home,
            client=make_client(phone_number="+998991234568"),
            company=self.company,        )
        resp = self.client.get(self.list_url, {"home_id": self.home.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_create_booking_via_api(self):
        data = {
            "home": self.home.id,
            "client": self.client_obj.id,
            "company": self.company.id,
            "home_status": Home.HomeStatus.RESERVED,
        }
        resp = self.client.post(self.list_url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Booking.objects.filter(home=self.home).exists())

    def test_create_booking_computes_calculator_on_backend(self):
        from calculator.models import GuaranteeOption, SubsidyOption
        self.home.area = Decimal("49.35")
        self.home.price_per_sqm = Decimal("7700000")
        self.home.save()
        guarantee = GuaranteeOption.objects.get(key="kafillik")
        subsidy = SubsidyOption.objects.get(key="oddiy")
        data = {
            "home": self.home.id,
            "client": self.client_obj.id,
            "company": self.company.id,
            "home_status": Home.HomeStatus.RESERVED,
            "payment_type": Booking.PaymentType.BOSH_TOLOVLI,
            "guarantee_id": guarantee.id,
            "subsidy_id": subsidy.id,
            "credit_years": 20,
            "contract_price": "1",
            "credit_amount": "1",
        }
        resp = self.client.post(self.list_url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        booking = Booking.objects.get(home=self.home)
        self.assertEqual(booking.contract_price, Decimal("379995000"))
        self.assertEqual(booking.client_payment, Decimal("27000000"))
        self.assertEqual(booking.credit_amount, Decimal("322995000"))
        self.assertEqual(booking.subsidy_amount, Decimal("30000000"))
        self.assertEqual(booking.guarantee_percent, Decimal("15.00"))
        self.assertEqual(booking.monthly_full, Decimal("4737692"))
        self.assertEqual(booking.monthly_stage1, Decimal("4016510"))
        self.assertEqual(booking.gov_monthly, Decimal("721182"))

    def test_delete_booking_via_api(self):
        booking = Booking.objects.create(
            home=self.home, client=self.client_obj, company=self.company        )
        url = reverse("booking-detail", args=[booking.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Booking.objects.filter(id=booking.id).exists())

    def test_retrieve_booking(self):
        booking = Booking.objects.create(
            home=self.home, client=self.client_obj, company=self.company        )
        url = reverse("booking-detail", args=[booking.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], booking.id)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PaymentViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username='pay_api')
        self.client.force_authenticate(user=self.user)
        self.home = make_home(price_per_sqm=1000, area=50)
        self.booking = make_booking(home=self.home)
        self.list_url = reverse('payment-list')

    def _create_payment(self, amount):
        resp = self.client.post(self.list_url, {
            'booking': self.booking.id,
            'amount': str(amount),
        })
        return resp

    def test_create_payment_returns_201(self):
        resp = self._create_payment(10000)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_payment_exceeding_debt_rejected(self):
        resp = self._create_payment(99999999)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', resp.data)

    def test_remaining_debt_decreases_after_payment(self):
        from booking.models import Payment
        resp = self._create_payment(10000)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        payment_id = resp.data['id']
        payment = Payment.objects.get(id=payment_id)
        self.assertEqual(payment.booking.remaining_debt, self.booking.total_price - 10000)

    def test_update_payment_amount(self):
        from booking.models import Payment
        self._create_payment(10000)
        payment = Payment.objects.filter(booking=self.booking).first()
        url = reverse('payment-detail', args=[payment.id])
        resp = self.client.put(url, {'booking': self.booking.id, 'amount': '5000'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        payment.refresh_from_db()
        self.assertEqual(payment.amount, 5000)

    def test_update_payment_amount_exceeding_debt_rejected(self):
        from booking.models import Payment
        self._create_payment(10000)
        payment = Payment.objects.filter(booking=self.booking).first()
        url = reverse('payment-detail', args=[payment.id])
        resp = self.client.put(url, {'booking': self.booking.id, 'amount': '99999999'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', resp.data)

    def test_update_payment_remaining_debt_correct(self):
        from booking.models import Payment
        self._create_payment(10000)
        payment = Payment.objects.filter(booking=self.booking).first()
        url = reverse('payment-detail', args=[payment.id])
        self.client.put(url, {'booking': self.booking.id, 'amount': '20000'})
        payment.refresh_from_db()
        self.booking.refresh_from_db()
        expected = self.booking.total_price - 20000
        self.assertEqual(self.booking.remaining_debt, expected)

    def test_delete_payment_returns_204(self):
        from booking.models import Payment
        self._create_payment(10000)
        payment = Payment.objects.filter(booking=self.booking).first()
        url = reverse('payment-detail', args=[payment.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Payment.objects.filter(id=payment.id).exists())

    def test_delete_payment_increases_remaining_debt(self):
        from booking.models import Payment
        total = self.booking.total_price
        self._create_payment(10000)
        payment = Payment.objects.filter(booking=self.booking).first()
        url = reverse('payment-detail', args=[payment.id])
        self.client.delete(url)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.remaining_debt, total)

    def test_remaining_debt_includes_renovation(self):
        from booking.models import Booking
        from projects.models.project_models import Renovation
        ren = Renovation.objects.create(title="Lux", price=Decimal("7000"))
        home = make_home(home_number=321, price_per_sqm=1000, area=50, renovation=ren)
        booking = Booking.objects.create(
            home=home, client=make_client(phone_number="+998900000321"), company=make_company())
        self.assertEqual(booking.total_price, Decimal("57000"))
        self.assertEqual(booking.remaining_debt, Decimal("57000"))

    def test_cannot_pay_when_debt_fully_covered(self):
        total = int(self.booking.total_price)
        self._create_payment(total)
        resp = self._create_payment(1)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
