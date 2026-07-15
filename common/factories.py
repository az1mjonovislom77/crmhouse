"""Testlar uchun umumiy factory funksiyalar.

Har bir app o'zining tests.py'sida shu factorylarni ishlatadi;
app'ga xos fixture'lar (make_lead, make_card, ...) o'z faylida qoladi.
"""

from booking.models import Company
from client.models import Client
from home.models import Home
from projects.models.project_models import Block, Floors, Project, Renovation
from user.models import User


def make_user(**kwargs):
    password = kwargs.pop("password", "pass123")
    defaults = {"username": "test_user", "full_name": "Test User", "role": User.UserRoles.SELLER, "is_staff": True}
    defaults.update(kwargs)
    u = User(**defaults)
    u.set_password(password)
    u.save()
    return u


def make_project(**kwargs):
    defaults = {"title": "Test Project", "description": "Desc", "floors": 5}
    defaults.update(kwargs)
    return Project.objects.create(**defaults)


def make_blocks(**kwargs):
    if "projects" not in kwargs:
        kwargs["projects"] = make_project()
    defaults = {"title": "Block A"}
    defaults.update(kwargs)
    return Block.objects.create(**defaults)


def make_floors(**kwargs):
    defaults = {"number": 1}
    defaults.update(kwargs)
    return Floors.objects.create(**defaults)


def make_renovation(**kwargs):
    defaults = {"title": "Standard", "price": 1000}
    defaults.update(kwargs)
    return Renovation.objects.create(**defaults)


def make_home(**kwargs):
    defaults = {"home_number": 1, "home_status": Home.HomeStatus.AVAILABLE, "price_per_sqm": 500, "area": 50}
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
