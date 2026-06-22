from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from home.models import Home
from projects.models.project_models import Block, Floors, Project, Renovation
from projects.models.showroom_models import Showroom, SVG
from projects.selectors.projects_selectors import get_projects_with_stats
from projects.selectors.showroom_selectors import get_blocks_stats
from projects.services.project_service import ProjectService
from user.models import User


def make_user(**kwargs):
    password = kwargs.pop("password", "pass123")
    defaults = {"username": "pr_user", "full_name": "PR User", "role": User.UserRoles.SELLER}
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
    defaults = {"title": "Block A", "image": "fake.webp"}
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


class ProjectsModelTest(TestCase):
    def test_create_project(self):
        project = make_project(title="My Project")
        self.assertEqual(project.title, "My Project")
        self.assertIsNotNone(project.pk)

    def test_project_str(self):
        project = make_project(title="Hero Project")
        self.assertEqual(str(project), "Hero Project")

    def test_project_ordered_by_newest(self):
        p1 = make_project(title="P1")
        p2 = make_project(title="P2")
        projects = list(Project.objects.all())
        self.assertEqual(projects[0].pk, p2.pk)


class BlocksModelTest(TestCase):
    def test_create_blocks(self):
        blocks = make_blocks(title="Block B")
        self.assertEqual(blocks.title, "Block B")

    def test_blocks_str(self):
        blocks = make_blocks(title="Block C")
        self.assertEqual(str(blocks), "Block C")

    def test_blocks_linked_to_project(self):
        project = make_project(title="Linked Project")
        blocks = make_blocks(projects=project, title="B1")
        self.assertEqual(blocks.projects, project)


class FloorsModelTest(TestCase):
    def test_create_floor(self):
        floor = Floors.objects.create(number=5)
        self.assertEqual(floor.number, 5)

    def test_floor_str(self):
        floor = Floors.objects.create(number=3)
        self.assertEqual(str(floor), "3")


class RenovationModelTest(TestCase):
    def test_create_renovation(self):
        ren = Renovation.objects.create(title="Luxury", price=5000)
        self.assertEqual(ren.title, "Luxury")
        self.assertEqual(ren.price, 5000)

    def test_renovation_str(self):
        ren = Renovation.objects.create(title="Basic", price=0)
        self.assertEqual(str(ren), "Basic")


class ProjectServiceTest(TestCase):
    def test_create_project_without_image(self):
        project = ProjectService.create_project({
            "title": "No Image", "description": "Desc", "floors": 3
        })
        self.assertIsNotNone(project.pk)
        self.assertEqual(project.title, "No Image")

    def test_update_project_fields(self):
        project = make_project(title="Old Title")
        updated = ProjectService.update_project(project, {"title": "New Title", "description": "D", "floors": 2})
        project.refresh_from_db()
        self.assertEqual(project.title, "New Title")

    def test_update_project_returns_instance(self):
        project = make_project()
        result = ProjectService.update_project(project, {"title": "T", "description": "D", "floors": 1})
        self.assertEqual(result.pk, project.pk)


class ProjectsSelectorTest(TestCase):
    def setUp(self):
        self.project = make_project(title="Stats Project")
        self.blocks = make_blocks(projects=self.project, title="SB")
        Home.objects.create(blocks=self.blocks, home_number=1,
                            home_status=Home.HomeStatus.AVAILABLE, price_per_sqm=0, area=0)
        Home.objects.create(blocks=self.blocks, home_number=2,
                            home_status=Home.HomeStatus.SOLD, price_per_sqm=0, area=0)

    def test_returns_projects(self):
        qs = get_projects_with_stats()
        pks = [p.pk for p in qs]
        self.assertIn(self.project.pk, pks)

    def test_annotates_homes_count(self):
        project = get_projects_with_stats().get(pk=self.project.pk)
        self.assertEqual(project.homes_count, 2)

    def test_annotates_sold_homes(self):
        project = get_projects_with_stats().get(pk=self.project.pk)
        self.assertEqual(project.sold_homes, 1)

    def test_annotates_available_homes(self):
        project = get_projects_with_stats().get(pk=self.project.pk)
        self.assertEqual(project.available_homes, 1)


class ShowroomSelectorTest(TestCase):
    def setUp(self):
        self.project = make_project(title="SR Project")
        self.blocks = make_blocks(projects=self.project, title="SR Block")
        self.showroom = Showroom.objects.create(
            block=self.blocks,
            blocks_number=1,
            path="M0,0",
            navigate_to="/path",
            hover_color="#fff",
            default_color="#000",
        )

    def test_returns_showrooms(self):
        qs = get_blocks_stats()
        pks = [s.pk for s in qs]
        self.assertIn(self.showroom.pk, pks)

    def test_select_related_blocks_projects(self):
        showroom = get_blocks_stats().get(pk=self.showroom.pk)
        with self.assertNumQueries(0):
            _ = showroom.block.projects.title


class ProjectsViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="pr_api")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("projects-list")

    def test_list_projects(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_project(self):
        project = make_project(title="Retrieve Project")
        url = reverse("projects-detail", args=[project.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_project(self):
        project = make_project(title="Delete Me")
        url = reverse("projects-detail", args=[project.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(id=project.id).exists())


class BlocksViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="bl_api")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("blocks-list")

    def test_list_blocks(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_block(self):
        blocks = make_blocks(title="My Block")
        url = reverse("blocks-detail", args=[blocks.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_block(self):
        blocks = make_blocks(title="Del Block")
        url = reverse("blocks-detail", args=[blocks.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class FloorsViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="fl_api")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("floors-list")

    def test_list_floors(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_floor(self):
        resp = self.client.post(self.url, {"number": 10})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Floors.objects.filter(number=10).exists())

    def test_delete_floor(self):
        floor = Floors.objects.create(number=99)
        url = reverse("floors-detail", args=[floor.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


class RenovationViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="rv_api")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("renovation-list")

    def test_list_renovations(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_renovation(self):
        resp = self.client.post(self.url, {"title": "Premium", "price": "3000.00"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Renovation.objects.filter(title="Premium").exists())

    def test_update_renovation(self):
        ren = Renovation.objects.create(title="Old", price=0)
        url = reverse("renovation-detail", args=[ren.id])
        resp = self.client.put(url, {"title": "New", "price": "500.00"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ren.refresh_from_db()
        self.assertEqual(ren.title, "New")

    def test_delete_renovation(self):
        ren = Renovation.objects.create(title="Del", price=0)
        url = reverse("renovation-detail", args=[ren.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


class ShowroomViewTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="sm_api")
        self.client.force_authenticate(user=self.user)

    def test_showroom_authenticated(self):
        resp = self.client.get("/projects/showroom/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_showroom_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get("/projects/showroom/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
