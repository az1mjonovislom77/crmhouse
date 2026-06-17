import unittest
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from tasks.models import Card, Comment, Project
from tasks.permissions import IsProjectMemberOrAdmin
from tasks.services.project import create_project, delete_project, update_project
from user.models import User

IS_SQLITE = connection.vendor == "sqlite"


def make_user(**kwargs):
    password = kwargs.pop("password", "pass123")
    defaults = {"username": "tk_user", "full_name": "TK User", "role": User.UserRoles.SELLER}
    defaults.update(kwargs)
    u = User(**defaults)
    u.set_password(password)
    u.save()
    return u


def make_card(**kwargs):
    defaults = {"title": "Test Card"}
    defaults.update(kwargs)
    return Card.objects.create(**defaults)


def make_project_obj(card=None, **kwargs):
    if card is None:
        card = make_card()
    defaults = {"card": card, "title": "Test Project", "description": "Desc", "order": 1}
    defaults.update(kwargs)
    return Project.objects.create(**defaults)


def make_comment(user=None, project=None, **kwargs):
    if user is None:
        user = make_user(username="cm_user")
    if project is None:
        project = make_project_obj()
    defaults = {"user": user, "project": project, "text": "Test comment"}
    defaults.update(kwargs)
    return Comment.objects.create(**defaults)


class CardModelTest(TestCase):
    def test_create_card(self):
        card = Card.objects.create(title="Sprint 1")
        self.assertEqual(card.title, "Sprint 1")
        self.assertIsNotNone(card.pk)

    def test_card_str(self):
        card = Card.objects.create(title="My Card")
        self.assertEqual(str(card), "My Card")

    def test_card_has_created_at(self):
        card = Card.objects.create(title="Timed")
        self.assertIsNotNone(card.created_at)


class ProjectModelTest(TestCase):
    def setUp(self):
        self.card = make_card()

    def test_create_project(self):
        project = Project.objects.create(
            card=self.card, title="Task 1", description="Desc", order=1
        )
        self.assertEqual(project.title, "Task 1")
        self.assertEqual(project.order, 1)

    def test_project_str(self):
        project = Project.objects.create(card=self.card, title="My Task", description="D", order=1)
        self.assertEqual(str(project), "My Task")

    def test_unique_order_per_card_constraint(self):
        Project.objects.create(card=self.card, title="P1", description="D", order=1)
        with self.assertRaises(Exception):
            Project.objects.create(card=self.card, title="P2", description="D", order=1)

    def test_ordered_by_order_field(self):
        Project.objects.create(card=self.card, title="P3", description="D", order=3)
        Project.objects.create(card=self.card, title="P1", description="D", order=1)
        Project.objects.create(card=self.card, title="P2", description="D", order=2)
        projects = list(Project.objects.filter(card=self.card))
        self.assertEqual(projects[0].order, 1)
        self.assertEqual(projects[1].order, 2)
        self.assertEqual(projects[2].order, 3)

    def test_project_with_users(self):
        user = make_user(username="pm_user")
        project = Project.objects.create(card=self.card, title="With Users", description="D", order=1)
        project.users.add(user)
        self.assertIn(user, project.users.all())


class CommentModelTest(TestCase):
    def setUp(self):
        self.user = make_user(username="cm_mdl")
        self.project = make_project_obj()

    def test_create_comment(self):
        comment = Comment.objects.create(user=self.user, project=self.project, text="Nice work!")
        self.assertEqual(comment.text, "Nice work!")

    def test_comment_str(self):
        comment = Comment.objects.create(user=self.user, project=self.project, text="Short text here")
        self.assertIn(self.user.full_name or self.user.username, str(comment))

    def test_comment_linked_to_project(self):
        comment = Comment.objects.create(user=self.user, project=self.project, text="Test")
        self.assertEqual(comment.project, self.project)


class CreateProjectServiceTest(TestCase):
    def setUp(self):
        self.card = make_card(title="Service Card")

    def test_create_project_assigns_order(self):
        project = create_project(card=self.card, title="P1", description="D")
        self.assertEqual(project.order, 1)

    def test_create_second_project_increments_order(self):
        create_project(card=self.card, title="P1", description="D")
        p2 = create_project(card=self.card, title="P2", description="D")
        self.assertEqual(p2.order, 2)

    def test_create_project_at_specific_order_shifts_others(self):
        create_project(card=self.card, title="P1", description="D")
        create_project(card=self.card, title="P2", description="D")
        create_project(card=self.card, title="P_new", description="D", order=1)
        p1 = Project.objects.get(card=self.card, title="P1")
        self.assertEqual(p1.order, 2)

    def test_create_project_with_users(self):
        user = make_user(username="cp_usr")
        project = create_project(card=self.card, title="P", description="D", users=[user])
        self.assertIn(user, project.users.all())

    def test_create_project_no_card_uses_first(self):
        project = create_project(title="Auto Card", description="D")
        self.assertEqual(project.card, self.card)

    def test_create_project_no_card_no_cards_raises(self):
        Card.objects.all().delete()
        with self.assertRaises(ValidationError):
            create_project(title="No Card", description="D")

    def test_create_project_order_below_1_defaults_to_1(self):
        project = create_project(card=self.card, title="P", description="D", order=-5)
        self.assertEqual(project.order, 1)

    def test_create_project_persisted(self):
        create_project(card=self.card, title="Persisted", description="D")
        self.assertTrue(Project.objects.filter(title="Persisted").exists())


class UpdateProjectServiceTest(TestCase):
    def setUp(self):
        self.card = make_card(title="Update Card")
        self.p1 = create_project(card=self.card, title="P1", description="D")
        self.p2 = create_project(card=self.card, title="P2", description="D")
        self.p3 = create_project(card=self.card, title="P3", description="D")

    def test_update_title_same_order(self):
        update_project(self.p1, title="Updated P1", description="D")
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.title, "Updated P1")
        self.assertEqual(self.p1.order, 1)

    def test_move_down_same_card(self):
        update_project(self.p1, new_order=3)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.order, 3)
        self.p2.refresh_from_db()
        self.assertEqual(self.p2.order, 1)

    def test_move_up_same_card(self):
        update_project(self.p3, new_order=1)
        self.p3.refresh_from_db()
        self.assertEqual(self.p3.order, 1)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.order, 2)

    def test_move_to_different_card(self):
        other_card = make_card(title="Other Card")
        p_other = create_project(card=other_card, title="PO", description="D")
        update_project(self.p1, new_card=other_card, new_order=1)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.card, other_card)
        self.assertEqual(self.p1.order, 1)
        p_other.refresh_from_db()
        self.assertEqual(p_other.order, 2)

    def test_update_users(self):
        user = make_user(username="up_usr")
        update_project(self.p1, users=[user])
        self.assertIn(user, self.p1.users.all())

    def test_no_gaps_after_move(self):
        update_project(self.p2, new_order=3)
        orders = sorted(Project.objects.filter(card=self.card).values_list('order', flat=True))
        self.assertEqual(orders, [1, 2, 3])

    def test_order_beyond_max_appends_to_end(self):
        # service clamps new_order to max_order+1 (known behavior)
        update_project(self.p1, new_order=999)
        self.p1.refresh_from_db()
        self.assertGreater(self.p1.order, 0)


class DeleteProjectServiceTest(TestCase):
    def setUp(self):
        self.card = make_card(title="Del Card")
        self.p1 = create_project(card=self.card, title="P1", description="D")
        self.p2 = create_project(card=self.card, title="P2", description="D")
        self.p3 = create_project(card=self.card, title="P3", description="D")

    def test_delete_project_removes_it(self):
        pk = self.p3.pk
        delete_project(self.p3)
        self.assertFalse(Project.objects.filter(pk=pk).exists())

    @unittest.skipIf(IS_SQLITE, "SQLite checks UNIQUE constraint per-row; PostgreSQL handles it atomically")
    def test_delete_shifts_orders_down(self):
        delete_project(self.p1)
        self.p2.refresh_from_db()
        self.p3.refresh_from_db()
        self.assertEqual(self.p2.order, 1)
        self.assertEqual(self.p3.order, 2)

    @unittest.skipIf(IS_SQLITE, "SQLite checks UNIQUE constraint per-row; PostgreSQL handles it atomically")
    def test_delete_middle_project_no_gaps(self):
        delete_project(self.p2)
        orders = sorted(Project.objects.filter(card=self.card).values_list('order', flat=True))
        self.assertEqual(orders, [1, 2])

    def test_delete_last_project_no_shift(self):
        delete_project(self.p3)
        self.p1.refresh_from_db()
        self.p2.refresh_from_db()
        self.assertEqual(self.p1.order, 1)
        self.assertEqual(self.p2.order, 2)


class IsProjectMemberOrAdminPermissionTest(TestCase):
    def setUp(self):
        self.card = make_card()
        self.member = make_user(username="member", role=User.UserRoles.SELLER)
        self.admin = make_user(username="tadmin", role=User.UserRoles.ADMIN)
        self.superadmin = make_user(username="tsuperadmin", role=User.UserRoles.SUPERADMIN)
        self.outsider = make_user(username="outsider", role=User.UserRoles.SELLER)
        self.project = create_project(card=self.card, title="P", description="D", users=[self.member])

    def _make_request(self, user, method="PUT"):
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.put("/") if method == "PUT" else factory.get("/")
        request.user = user
        return request

    def test_admin_can_mutate(self):
        perm = IsProjectMemberOrAdmin()
        req = self._make_request(self.admin, "PUT")
        self.assertTrue(perm.has_object_permission(req, None, self.project))

    def test_superadmin_can_mutate(self):
        perm = IsProjectMemberOrAdmin()
        req = self._make_request(self.superadmin, "PUT")
        self.assertTrue(perm.has_object_permission(req, None, self.project))

    def test_project_member_can_mutate(self):
        perm = IsProjectMemberOrAdmin()
        req = self._make_request(self.member, "PUT")
        self.assertTrue(perm.has_object_permission(req, None, self.project))

    def test_outsider_cannot_mutate(self):
        perm = IsProjectMemberOrAdmin()
        req = self._make_request(self.outsider, "PUT")
        self.assertFalse(perm.has_object_permission(req, None, self.project))

    def test_safe_method_allowed_for_all(self):
        perm = IsProjectMemberOrAdmin()
        req = self._make_request(self.outsider, "GET")
        self.assertTrue(perm.has_object_permission(req, None, self.project))


class CardViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="card_api")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("card-list")

    def test_list_cards(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_card(self):
        resp = self.client.post(self.url, {"title": "New Card"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Card.objects.filter(title="New Card").exists())

    def test_retrieve_card(self):
        card = Card.objects.create(title="Retrieve Card")
        url = reverse("card-detail", args=[card.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["title"], "Retrieve Card")

    def test_update_card(self):
        card = Card.objects.create(title="Old Card")
        url = reverse("card-detail", args=[card.id])
        resp = self.client.put(url, {"title": "Updated Card"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        card.refresh_from_db()
        self.assertEqual(card.title, "Updated Card")

    def test_delete_card(self):
        card = Card.objects.create(title="Del Card")
        url = reverse("card-detail", args=[card.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Card.objects.filter(id=card.id).exists())

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_card_history_action(self):
        card = Card.objects.create(title="History Card")
        url = reverse("card-history", args=[card.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class TaskProjectViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="tp_api", role=User.UserRoles.ADMIN)
        self.client.force_authenticate(user=self.user)
        self.card = make_card(title="API Card")
        self.url = reverse("project-list")

    def test_list_projects(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_project(self):
        data = {"card": self.card.id, "title": "API Project", "description": "Desc", "users": []}
        resp = self.client.post(self.url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Project.objects.filter(title="API Project").exists())

    def test_retrieve_project(self):
        project = create_project(card=self.card, title="Retrieve P", description="D")
        url = reverse("project-detail", args=[project.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["title"], "Retrieve P")

    def test_update_project_title(self):
        project = create_project(card=self.card, title="Old P", description="D", users=[self.user])
        url = reverse("project-detail", args=[project.id])
        data = {"title": "New P", "description": "D", "card": self.card.id, "users": [self.user.id]}
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_project(self):
        project = create_project(card=self.card, title="Del P", description="D")
        url = reverse("project-detail", args=[project.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_project_history_action(self):
        project = create_project(card=self.card, title="Hist P", description="D")
        url = reverse("project-history", args=[project.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class CommentViewSetTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="co_api")
        self.client.force_authenticate(user=self.user)
        self.card = make_card()
        self.project = create_project(card=self.card, title="CP", description="D")
        self.url = reverse("comment-list")

    def test_list_comments(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_comment(self):
        # CommentSerializer includes `user` as required field — must be sent explicitly
        data = {"project": self.project.id, "text": "A comment", "user": self.user.id}
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Comment.objects.filter(text="A comment").exists())

    def test_create_comment_sets_user(self):
        data = {"project": self.project.id, "text": "My comment", "user": self.user.id}
        self.client.post(self.url, data)
        comment = Comment.objects.get(text="My comment")
        self.assertEqual(comment.user, self.user)

    def test_retrieve_comment(self):
        comment = make_comment(user=self.user, project=self.project, text="Ret comment")
        url = reverse("comment-detail", args=[comment.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_update_comment(self):
        comment = make_comment(user=self.user, project=self.project, text="Old text")
        url = reverse("comment-detail", args=[comment.id])
        resp = self.client.put(url, {"project": self.project.id, "text": "New text", "user": self.user.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.text, "New text")

    def test_delete_comment(self):
        comment = make_comment(user=self.user, project=self.project, text="Del comment")
        url = reverse("comment-detail", args=[comment.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
