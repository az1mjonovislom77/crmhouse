from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from booking.models import Booking, Company, PaymentTerm
from client.models import Client
from home.models import Home, HomeStatusHistory, FloorPlan
from home.selectors.history_selectors import get_home_history
from home.selectors.home_selectors import get_homes_with_finance
from home.services.home import HomeService
from projects.models.project_models import Block, Floors, Project, Renovation
from user.models import User


def make_user(**kwargs):
    password = kwargs.pop("password", "pass123")
    defaults = {"username": "hm_user", "full_name": "HM User", "role": User.UserRoles.SELLER}
    defaults.update(kwargs)
    u = User(**defaults)
    u.set_password(password)
    u.save()
    return u


def make_project(**kwargs):
    defaults = {"title": "Proj", "description": "D", "floors": 1}
    defaults.update(kwargs)
    return Project.objects.create(**defaults)


def make_blocks(**kwargs):
    if "projects" not in kwargs:
        kwargs["projects"] = make_project()
    defaults = {"title": "Block", "image": "f.webp"}
    defaults.update(kwargs)
    return Block.objects.create(**defaults)


def make_floors(**kwargs):
    defaults = {"number": 1}
    defaults.update(kwargs)
    return Floors.objects.create(**defaults)


def make_renovation(**kwargs):
    defaults = {"title": "Std", "price": 2000}
    defaults.update(kwargs)
    return Renovation.objects.create(**defaults)


def make_home(**kwargs):
    defaults = {
        "home_number": 1,
        "home_status": Home.HomeStatus.AVAILABLE,
        "price_per_sqm": 500,
        "area": 60,
    }
    defaults.update(kwargs)
    return Home.objects.create(**defaults)


def make_client(**kwargs):
    defaults = {"full_name": "Cl", "phone_number": "+998901234567", "passport": "AA1", "address": "T"}
    defaults.update(kwargs)
    return Client.objects.create(**defaults)


def make_company(**kwargs):
    defaults = {"name": "Co", "address": "A", "phone": "+998"}
    defaults.update(kwargs)
    return Company.objects.create(**defaults)


class HomeModelTest(TestCase):
    def test_create_home(self):
        home = make_home(home_number=10)
        self.assertEqual(home.home_number, 10)
        self.assertEqual(home.home_status, Home.HomeStatus.AVAILABLE)

    def test_home_str(self):
        home = make_home(home_number=5)
        self.assertIn("5", str(home))

    def test_default_status_is_available(self):
        home = Home.objects.create(home_number=1, price_per_sqm=0, area=0)
        self.assertEqual(home.home_status, Home.HomeStatus.AVAILABLE)

    def test_home_with_blocks_and_floor(self):
        blocks = make_blocks()
        floor = make_floors(number=3)
        home = make_home(blocks=blocks, floor=floor)
        self.assertEqual(home.blocks, blocks)
        self.assertEqual(home.floor, floor)

    def test_home_with_renovation(self):
        ren = make_renovation(price=5000)
        home = make_home(renovation=ren)
        self.assertEqual(home.renovation.price, 5000)


class HomeStatusHistoryModelTest(TestCase):
    def setUp(self):
        self.home = make_home()
        self.user = make_user(username="hist_user")
        self.client_obj = make_client()

    def test_create_history_entry(self):
        h = HomeStatusHistory.objects.create(
            home=self.home,
            client=self.client_obj,
            from_status=Home.HomeStatus.AVAILABLE,
            to_status=Home.HomeStatus.RESERVED,
            changed_by=self.user,
        )
        self.assertEqual(h.from_status, Home.HomeStatus.AVAILABLE)
        self.assertEqual(h.to_status, Home.HomeStatus.RESERVED)

    def test_history_ordered_by_newest(self):
        HomeStatusHistory.objects.create(home=self.home, to_status="reserved")
        HomeStatusHistory.objects.create(home=self.home, to_status="sold")
        entries = list(HomeStatusHistory.objects.filter(home=self.home))
        self.assertEqual(entries[0].to_status, "sold")


class HomeServiceCreateTest(TestCase):
    def test_create_home_basic(self):
        home = HomeService.create_home({
            "home_number": 7,
            "price_per_sqm": 300,
            "area": 45,
        })
        self.assertIsNotNone(home.pk)
        self.assertEqual(home.home_number, 7)

    def test_create_home_persisted(self):
        HomeService.create_home({"home_number": 8, "price_per_sqm": 0, "area": 0})
        self.assertTrue(Home.objects.filter(home_number=8).exists())

    def test_create_home_with_blocks(self):
        blocks = make_blocks()
        home = HomeService.create_home({
            "home_number": 9,
            "blocks": blocks,
            "price_per_sqm": 0,
            "area": 0,
        })
        self.assertEqual(home.blocks, blocks)


class HomeServiceUpdateTest(TestCase):
    def setUp(self):
        self.home = make_home(home_number=1, price_per_sqm=500, area=60)

    def test_update_home_changes_fields(self):
        HomeService.update_home(self.home, {"home_number": 99, "price_per_sqm": 500, "area": 60})
        self.home.refresh_from_db()
        self.assertEqual(self.home.home_number, 99)

    def test_update_home_returns_instance(self):
        result = HomeService.update_home(self.home, {"price_per_sqm": 600, "area": 60})
        self.assertEqual(result.pk, self.home.pk)

    def test_update_home_without_floorplans_does_not_delete(self):
        HomeService.update_home(self.home, {"home_number": 1, "price_per_sqm": 500, "area": 70})
        self.home.refresh_from_db()
        self.assertEqual(self.home.area, 70)


class HomeServiceChangeStatusTest(TestCase):
    def setUp(self):
        self.user = make_user(username="cs_user")
        self.client_obj = make_client()
        self.home = make_home(home_status=Home.HomeStatus.AVAILABLE)

    def test_change_status_updates_home(self):
        HomeService.change_status(
            home_id=self.home.id,
            new_status=Home.HomeStatus.RESERVED,
            user=self.user,
        )
        self.home.refresh_from_db()
        self.assertEqual(self.home.home_status, Home.HomeStatus.RESERVED)

    def test_change_status_creates_history(self):
        HomeService.change_status(
            home_id=self.home.id,
            new_status=Home.HomeStatus.SOLD,
            user=self.user,
        )
        self.assertTrue(
            HomeStatusHistory.objects.filter(
                home=self.home, to_status=Home.HomeStatus.SOLD
            ).exists()
        )

    def test_change_status_records_from_status(self):
        HomeService.change_status(
            home_id=self.home.id,
            new_status=Home.HomeStatus.RESERVED,
            user=self.user,
        )
        history = HomeStatusHistory.objects.get(home=self.home)
        self.assertEqual(history.from_status, Home.HomeStatus.AVAILABLE)

    def test_change_status_same_status_no_history(self):
        HomeService.change_status(
            home_id=self.home.id,
            new_status=Home.HomeStatus.AVAILABLE,
            user=self.user,
        )
        self.assertEqual(HomeStatusHistory.objects.filter(home=self.home).count(), 0)

    def test_change_status_records_client(self):
        HomeService.change_status(
            home_id=self.home.id,
            new_status=Home.HomeStatus.SOLD,
            user=self.user,
            client=self.client_obj,
        )
        history = HomeStatusHistory.objects.get(home=self.home)
        self.assertEqual(history.client, self.client_obj)

    def test_change_status_records_changed_by(self):
        HomeService.change_status(
            home_id=self.home.id,
            new_status=Home.HomeStatus.SOLD,
            user=self.user,
        )
        history = HomeStatusHistory.objects.get(home=self.home)
        self.assertEqual(history.changed_by, self.user)


class HomeSelectorTest(TestCase):
    def setUp(self):
        self.blocks = make_blocks()
        self.floor = make_floors()
        self.ren = make_renovation(price=1000)
        self.home = make_home(blocks=self.blocks, floor=self.floor, renovation=self.ren,
                              price_per_sqm=100, area=50)

    def test_get_homes_with_finance_returns_queryset(self):
        qs = get_homes_with_finance()
        self.assertIn(self.home, qs)

    def test_annotates_total_price(self):
        home = get_homes_with_finance().get(pk=self.home.pk)
        expected = (50 * 100) + 1000
        self.assertEqual(home.total_price_annotated, expected)

    def test_annotates_zero_when_no_renovation(self):
        plain_home = make_home(home_number=2, price_per_sqm=200, area=30)
        home = get_homes_with_finance().get(pk=plain_home.pk)
        self.assertEqual(home.total_price_annotated, 200 * 30)

    def test_select_related_blocks(self):
        qs = get_homes_with_finance()
        home = qs.get(pk=self.home.pk)
        with self.assertNumQueries(0):
            _ = home.blocks.title


class HomeHistorySelectorTest(TestCase):
    def setUp(self):
        self.user = make_user(username="hs_user")
        self.home = make_home()
        HomeStatusHistory.objects.create(home=self.home, to_status="reserved", changed_by=self.user)
        HomeStatusHistory.objects.create(home=self.home, to_status="sold", changed_by=self.user)

    def test_returns_history_for_home(self):
        qs = get_home_history(home_id=self.home.id)
        self.assertEqual(qs.count(), 2)

    def test_filters_by_user(self):
        other_user = make_user(username="hs_other")
        HomeStatusHistory.objects.create(home=self.home, to_status="available", changed_by=other_user)
        qs = get_home_history(home_id=self.home.id, user_id=self.user.id)
        for entry in qs:
            self.assertEqual(entry.changed_by, self.user)

    def test_ordered_newest_first(self):
        qs = list(get_home_history(home_id=self.home.id))
        self.assertGreaterEqual(qs[0].changed_at, qs[-1].changed_at)

    def test_select_related_included(self):
        qs = get_home_history(home_id=self.home.id)
        entry = qs.first()
        with self.assertNumQueries(0):
            _ = entry.changed_by.username


class HomeViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="hm_api")
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse("home-list")
        self.blocks = make_blocks()
        self.floor = make_floors()

    def test_list_homes(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filter_by_home_status(self):
        make_home(home_number=10, home_status=Home.HomeStatus.SOLD)
        make_home(home_number=11, home_status=Home.HomeStatus.AVAILABLE)
        resp = self.client.get(self.list_url, {"home_status": Home.HomeStatus.SOLD})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data:
            self.assertEqual(item["home_status"], Home.HomeStatus.SOLD)

    def test_retrieve_home(self):
        home = make_home(home_number=50)
        url = reverse("home-detail", args=[home.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["home_number"], 50)

    def test_history_action(self):
        home = make_home(home_number=55)
        HomeStatusHistory.objects.create(home=home, to_status="reserved", changed_by=self.user)
        url = reverse("home-history", args=[home.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_delete_home(self):
        home = make_home(home_number=77)
        url = reverse("home-detail", args=[home.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Home.objects.filter(id=home.id).exists())


class HomeHistoryListAPIViewTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="hhl_api")
        self.client.force_authenticate(user=self.user)
        self.home = make_home()
        self.url = "/home/home-history/"

    def test_list_history_authenticated(self):
        HomeStatusHistory.objects.create(home=self.home, to_status="reserved", changed_by=self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filter_by_to_status(self):
        HomeStatusHistory.objects.create(home=self.home, to_status="reserved")
        HomeStatusHistory.objects.create(home=self.home, to_status="sold")
        resp = self.client.get(self.url, {"to_status": "sold"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data["data"]:
            self.assertEqual(item["to_status"], "sold")

    def test_filter_by_date_from(self):
        HomeStatusHistory.objects.create(home=self.home, to_status="reserved")
        resp = self.client.get(self.url, {"from": "2020-01-01"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_pagination_structure(self):
        resp = self.client.get(self.url)
        self.assertIn("data", resp.data)
        self.assertIn("total", resp.data)
        self.assertIn("page", resp.data)
